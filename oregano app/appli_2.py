from flask import Flask,flash,request,redirect,url_for,session,render_template,g
from werkzeug.utils import secure_filename
import os 
import pandas as pd
from metapub import PubMedFetcher
import requests
import pykeen
import torch
from pykeen.triples import TriplesFactory 
from pykeen.models.predict import get_tail_prediction_df
from pykeen.models.predict import get_head_prediction_df
from pykeen.models.predict import get_all_prediction_df
 
# dossier de telechargement du fichier importe
Repertoire_fichier_importé = "C:/Users/Lenovo/Desktop/Projet fichier/upload" 

#Dossier fichier de mapping
chemin_fichier_mapping = "C:/Users/Lenovo/Desktop/Projet fichier/staticFiles/fichier_ids_final.tsv"

#lire fichier mapping
map = pd.read_csv(chemin_fichier_mapping, sep="\t")

# Dicos entités pour les predictions 

Dic_effects={}
Dic_sideeff={}
Dic_activ ={}
Dic_indications={}
Dic_paths={}
Dic_target={}
Dic_pheno={}
Dic_gene={}
Dic_disease={}
Dic_comp ={}
#side 1
for i,r in map.iterrows():
    if "SIDE" in r["ID_OREGANO"]:
        if r["ID_OREGANO"] not in Dic_sideeff:
            Dic_sideeff[r["ID_OREGANO"]]=r["LIBELLE"]
Side_effects = []
for v in Dic_sideeff.values():
    Side_effects.append(v)
# effe 2
for i,r in map.iterrows():
    if "EFFECT" in r["ID_OREGANO"]:
        if r["ID_OREGANO"] not in Dic_sideeff and r["ID_OREGANO"] not in Dic_effects:
            Dic_effects[r["ID_OREGANO"]]=r["LIBELLE"]
effects = []
for v in Dic_effects.values():
    if v not in effects:
        effects.append(v)            
# gene 3
for i,r in map.iterrows():
    if "GENE" in r["ID_OREGANO"]:
        if r["ID_OREGANO"] not in Dic_gene:
            Dic_gene[r["ID_OREGANO"]]=r["LIBELLE"]
genes = []
for v in Dic_gene.values():
    if v not in genes:
        genes.append(v)
#pheno 4
for i,r in map.iterrows():
    if "PHENOTYPE" in r["ID_OREGANO"]:
        if r["ID_OREGANO"] not in Dic_pheno:
            Dic_pheno[r["ID_OREGANO"]]=r["LIBELLE"]
phenotypes = []          
for v in Dic_pheno.values():
    if v not in phenotypes:
        phenotypes.append(v)  
# path 5
for i,r in map.iterrows():
    if "PATHWAY" in r["ID_OREGANO"]:
        if r["ID_OREGANO"] not in Dic_paths:
            Dic_paths[r["ID_OREGANO"]]=r["LIBELLE"]
pathways = []
for v in Dic_paths.values():
    if v not in pathways:
        pathways.append(v)
#target 6
for i,r in map.iterrows():
    if "PROTEIN" in r["ID_OREGANO"] or "MOLECULE" in r["ID_OREGANO"] :
        if r["ID_OREGANO"] not in Dic_target:
            Dic_target[r["ID_OREGANO"]]=r["LIBELLE"]
targets = []
for v in Dic_target.values():
    if v not in targets:
        targets.append(v)
#indica 7
for i,r in map.iterrows():
    if "INDICATION" in r["ID_OREGANO"]:
        if r["ID_OREGANO"] not in Dic_indications:
            Dic_indications[r["ID_OREGANO"]]=r["LIBELLE"]
indications = []
for v in Dic_indications.values():
    if v not in indications:
        indications.append(v)
# activity 8
for i,r in map.iterrows():
    if "ACTIVITY" in r["ID_OREGANO"]:
        if r["ID_OREGANO"] not in Dic_activ:
            Dic_activ[r["ID_OREGANO"]]=r["LIBELLE"]          
activities = []
for v in Dic_activ.values():
    if v not in activities:
        activities.append(v)
#compound 9
for i,r in map.iterrows():
    if "COMPOUND" in r["ID_OREGANO"]:
        if r["ID_OREGANO"] not in Dic_comp:
            Dic_comp[r["ID_OREGANO"]]=r["LIBELLE"]
compounds = []
for v in Dic_comp.values():
    if v not in compounds:
        compounds.append(v)
#disea 10            
for i,r in map.iterrows():
    if "DISEASE" in r["ID_OREGANO"]:
        if r["ID_OREGANO"] not in Dic_disease:
            Dic_disease[r["ID_OREGANO"]]=r["LIBELLE"]
diseases = []
for v in Dic_disease.values():
    if v not in diseases:
        diseases.append(v)


#extensions qui sont autorisées pour l'importation
Extensions_autorisees = {"tsv"}

#initialisation de l'application
app = Flask(__name__)
app.secret_key="code secret"

#configuration de l'application POUR CHARGEMENT de fichier
app.config["REPERTOIRE_FICHIER_IMPORTE"] = Repertoire_fichier_importé

#fonction qui verifie l'extension du fichier importé :  renvoie des booleens(true or false)
def verifier_extension(nomfichier):
    return "." in nomfichier and nomfichier.rsplit(".",1)[1].lower() in Extensions_autorisees # verifie si il y a un point dans le nom du fichier,renvoie les lettres du nom apres le dernier point qu'il contient,les change en miniscules et verifie qu'elles sont dans le set des extensions autorisees

#definition d'une route
@app.route("/", methods=["GET", "POST"])

def charger_fichier():
    if request.method == "POST" :
        #Verifier que le champ de fichier est bien present dans la requete POST, donc si le champ de fichier n'a pas du tout ete touche (request.files est un dictionnaire)
        if "file" not in request.files : #file est le name donné a l'input de type file dans HTML/ 
            flash("Aucun fichier trouvé dans la requete") # flash sert a envoyer des messages a l'utilisateur
            return redirect(request.url) # renvoie vers l'URL de la requete pour reessayer le chargement

        fichier = request.files["file"] # si champ du fichier fichier present dans la requete, l'enregistrer dans la variable fichier

        # On verifie par la suite que l'utilisateur a bien selectionne un fichier (donc si le nom du fichier existe bien)
        if fichier.filename == "" :
            flash("Aucun fichier selectionné")
            return redirect(request.url)
        
        if fichier and verifier_extension(fichier.filename) : # si le fichier a ete selectionne et l'extension est autorisee 
            nom_fichier = secure_filename(fichier.filename) #supprime les caracteres sppeciaux du nom de fichier
            fichier.save(os.path.join(app.config["REPERTOIRE_FICHIER_IMPORTE"],nom_fichier)) # sauvegarder le fichier dans le repertoire
            session['REPERTOIRE_FICHIER_IMPORTE'] = os.path.join(app.config['REPERTOIRE_FICHIER_IMPORTE'],nom_fichier)
            return render_template('index2.html')
	
    return render_template("index.html")

#affichage du contenu du fichier

@app.route("/affichage")
def afficher_fichier():
    # chemin du fichier importé
    chemin_fichier = session.get('REPERTOIRE_FICHIER_IMPORTE', None)

    # transformation en dataframe
    fichier_chargé = pd.read_csv(chemin_fichier,sep="\t",header=None)
    
    # lecture du fichier mapping IDs et libelle
    fichier_mapping= pd.read_csv(chemin_fichier_mapping,sep="\t")

    # creation d'un dictionnaire avec les paires id:libelle, #zip cree des tuples de chaque paire
    Dic_id_libelle=dict(zip(fichier_mapping["ID_OREGANO"],fichier_mapping["LIBELLE"]))  

    # Remplacer les IDs par leur libelle dans le fichier importe
    fichier_chargé[1] = fichier_chargé[1].map(Dic_id_libelle)
    fichier_chargé[4] = fichier_chargé[4].map(Dic_id_libelle)
    
    #listes deroulantes
    liste_deroulante_1 = []
    liste_deroulante_2 =[]

    #remplir les listes 
    for i,r in fichier_chargé.iterrows():
        if r[1] not in liste_deroulante_1 :
            liste_deroulante_1.append(r[1])
        if r[4] not in liste_deroulante_2 : 
            liste_deroulante_2.append(r[4])    


    #renommer les colonnes du fichier
    fichier_chargé = fichier_chargé.rename(columns = {0 : " ID", 1:"Libellé Entité (sujet)", 2:"Score",3:"Présence dans la base d'entrainement",4:"Libellé Entité (Objet)"})
    
    # transformation du df en format html
    fichier_chargé_html =  fichier_chargé.to_html(classes='predictions-table')

    return render_template("index3.html", tableau =fichier_chargé_html, liste_1= liste_deroulante_1, liste_2=liste_deroulante_2 )  

#@app.route("/affichage")
def recuperer_valeur_sujet():
        valeur_head = request.form.get("heads")
        return str(valeur_head)

def recuperer_valeur_objet():
    valeur_tail = request.form.get("tails")
    return str(valeur_tail)


#fonction pour recevoir les valeurs de JS
@app.route('/submit', methods=['POST'])
def submit():
    data = request.get_json()
    selected_value_sujet = data.get('heads', '')
    g.selected_value_sujet = selected_value_sujet
    print(selected_value_sujet)
    return selected_value_sujet

#trouver synonyme des termes pour la recherche bibliograhique
def trouver_synonyme(terme):
    response0 = requests.get("https://uts-ws.nlm.nih.gov/rest/search/current?string="+terme+"&apiKey=965c992f-e231-418c-8833-f4801083130d&searchType=exact")
    resultats=response0.json()
    Cui=[]
    Atoms=[]
    concepts = resultats["result"]["results"]
    for concept in concepts:
        Cui.append(concept["ui"])
    for ui in Cui :
        response1=requests.get("https://uts-ws.nlm.nih.gov/rest/content/current/CUI/"+ui+"/atoms?language=ENG&apiKey=965c992f-e231-418c-8833-f4801083130d")
        resultats1=response1.json()
        for element in resultats1["result"]:
            if element["name"] not in Atoms :
                Atoms.append(element["name"])
    return Atoms


@app.route("/affichage/articlesPubmed", methods=['GET', 'POST'])
def Recherche_pubmed():    
           
        #creer liste de synonymes des libelles de maladie et composes
        liste_synonymes_sujet = trouver_synonyme("quinidine")
        #liste_synonymes_objet = trouver_synonyme(objet)

        #verification
        #print(liste_synonymes_objet)
        print(liste_synonymes_sujet)

        #inserer OR entre les elements de la liste
        synonymes_compose = " OR ".join(liste_synonymes_sujet)
       # synonymes_maladie = " OR ".join(liste_synonymes_objet)
        
    
        # equation de recherche
        keyword = "("+ synonymes_compose +")" #+" AND " + "(" + synonymes_maladie +")"  
        num_of_articles = 10
        
        fetch = PubMedFetcher() # instanciation de la classe PubMedFetcher

        # obtenir les PMID des articles resultant de la recherche/ methode pmids_for_query(a,b)
        pmids = fetch.pmids_for_query(keyword, retmax = num_of_articles)

        # obtenir les articles
        articles = {} 
        for pmid in pmids:
            articles[pmid] = fetch.article_by_pmid(pmid) # methode article_by_pmid(x)
        
        titles = {}
        for pmid in pmids:
            titles[pmid] = fetch.article_by_pmid(pmid).title
        Title = pd.DataFrame(list(titles.items()), columns=["pmid", "Title"])
        
        abstracts = {}
        for pmid in pmids:
            abstracts[pmid] = fetch.article_by_pmid(pmid).abstract
        Abstract = pd.DataFrame(list(abstracts.items()), columns=["pmid", "abstract"])
        
        Authors = {}
        for pmid in pmids:
            Authors[pmid] = fetch.article_by_pmid(pmid).authors
        Author = pd.DataFrame(list(Authors.items()), columns=["pmid", "Authors"])
        
        years = {}
        for pmid in pmids:
            years[pmid] = fetch.article_by_pmid(pmid).year
        year = pd.DataFrame(list(years.items()), columns=["pmid", "year"])

        volumes = {}
        for pmid in pmids:
            volumes[pmid] = fetch.article_by_pmid(pmid).volume
        Volume = pd.DataFrame(list(volumes.items()), columns=["pmid", "volume"])
        
        issues = {}
        for pmid in pmids:
            issues[pmid] = fetch.article_by_pmid(pmid).issue
        Issue = pd.DataFrame(list(issues.items()), columns=["pmid", "issue"])
        
        links = {}
        for pmid in pmids:
            links[pmid] = "https://pubmed.ncbi.nlm.nih.gov/" + pmid + "/"
        Link = pd.DataFrame(list(links.items()), columns=["pmid", "link"])
        
        citations = {}
        for pmid in pmids:
            citations[pmid] = fetch.article_by_pmid(pmid).citation
        Citation = pd.DataFrame(list(citations.items()), columns=["pmid", "citations"])
        
        journals = {}
        for pmid in pmids:
            journals[pmid] = fetch.article_by_pmid(pmid).journal
        Journal = pd.DataFrame(list(journals.items()), columns=["pmid", "journal"])
        
        from functools import reduce
        Data_frames = [Title, Abstract, Author, year, Volume, Journal, Issue, Citation, Link]
        Data_frames_merged = reduce(lambda left, right: pd.merge(left, right, on="pmid"), Data_frames)
        final_data = Data_frames_merged[["Title","abstract","link"]]
        
        if final_data.empty:
            # Si final_data vide, afficher a message indiquant que pas d'articles trouvés 
            #messagebox.showinfo("Articles PubMed", "Aucun article trouvé")
            pass
        else:           
            final_data_html = final_data.to_html() 
            return render_template("index4.html",tableau = final_data_html)

@app.route("/affichage/articlesGoogleScholar", methods=['GET', 'POST'])
def Recherche_Googlescholar():
    from scholarly import scholarly
    
    #Recuperer les resultats d'une recherche GS

    #Equation de recherche
    search_query = scholarly.search_pubs("health")
    #il s'agit d'un itérateur
    
    #récuperer le premier resultat de la recherche
    articles={}
    
    try:
        for i in range(10):
            publication = next(search_query)
            articles[i]=publication["bib"]
    except StopIteration :
        # Si aucun resultat, afficher a message indiquant que pas d'articles trouvés 
        pass
    else :
        #sinon recuperer les articles 
        titles = {}
        print(articles)
        for article in articles:
            titles[article]=articles[article]["title"]
        title = pd.DataFrame(list(titles.items()),columns=["0","title"])

        authors ={}
        for article in articles :
            authors[article]=articles[article]["author"]
        author = pd.DataFrame(list(authors.items()),columns=["0","authors"])

        abstracts ={}
        for article in articles :
            abstracts[article]=articles[article]["abstract"]
        abstract = pd.DataFrame(list(abstracts.items()),columns=["0","abstract"])

        years ={}
        for article in articles :
            years[article]=articles[article]["pub_year"]
        year = pd.DataFrame(list(years.items()),columns=["0","year"])

        from functools import reduce
        Data_frame = [title,abstract,author,year]
        Data_frame_merged = reduce(lambda left,right: pd.merge(left,right, on="0"),Data_frame)
        Data_frame_merged_html = Data_frame_merged.to_html()

        # Creation de la table pour afficher les articles
        return render_template("index5.html", tableau = Data_frame_merged_html)

#changer les valeurs de liste deroulante
@app.route('/get_options', methods=['POST'])
def update_valeurs_liste():
    selected_value = request.form.get('selected_value')
    
    if selected_value == 'fruits':
        options = ['Apple', 'Banana', 'Cherry']
    elif selected_value == 'vegetables':
        options = ['Carrot', 'Broccoli', 'Spinach']
    else:
        options = []

    return jsonify(options)


#predictions
@app.route("/")
def predire_sujet():
    #charger le modele pre-entrainé
    my_pykeen_model = torch.load("C:/Users/Lenovo/Desktop/Projet fichier/staticFiles/trained_model.pkl",map_location=torch.device('cpu'))
    # recuperer les triplets
    training = TriplesFactory.from_path("C:/Users/Lenovo/Desktop/Projet fichier/staticFiles/SR_entier_Tr4_training_oregano.tsv")
    # fichier mapping 
  
 

#routes pour prediction
@app.route("/predictionsujets", methods = ["GET"])
def predictions_sujets():
    return render_template("predictionssujet.html")

@app.route("/predictionobjets", methods = ["GET"])
def predictions_objets():
    return render_template("predictionsobjet.html")

@app.route('/predictionrelations', methods = ["GET"])
def predictions_relations():
    return render_template("predictionsrelation.html")

@app.route('/predictioncomplete')
def predictions_completes():
    pass

#execution
if __name__== "__main__":
    app.run(debug=True)                                              







 



 