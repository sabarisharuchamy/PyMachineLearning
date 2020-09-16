import numpy as np
from flask import Flask, request, jsonify, render_template
import pickle
import pandas as pd
from instacrawler import crawler
app = Flask(__name__)
model = pickle.load(open('model.pkl', 'rb'))

@app.route('/')
def home():
    return render_template('index2.html')

@app.route('/instacrawl',methods=['POST'])
def instacrawl():
    if request.method == "POST":
        req = request.form
        instaid = req.get("instaid")
        test= preprocess(crawler.get_profile(instaid),instaid)
        test['prediction_text']=predict(test)
    return render_template('index.html',data=test)

def preprocess(data,instaid):
    processedData={}
    if len(data["photo_url"]) == 0:
        processedData["profile_pic"]=0
    else:
        processedData["profile_pic"]=1
    processedData["nums_length_username"]=len(instaid)/100
    processedData["fullname_words"]=len(data["name"].split())
    if len(data["name"]) == 0:
        processedData["nums_length_fullname"]=0
    else:
        processedData["nums_length_fullname"]=len(data["name"])/100
    if data["name"]==instaid:
        processedData["name_username"]=1
    else:
        processedData["name_username"]=0
    processedData["description_length"]=len(data["desc"])
    processedData["external_URL"]=0
    processedData["private"]=0
    processedData["posts"]=data["post_num"]
    processedData["followers"]=data["follower_num"]
    processedData["follows"]=data["following_num"]
    return processedData

def predict(test):

    #final_features = [float(x) for x in request.form.values()]
    final_features = [float(x) for x in test.values()]
    dfObj = pd.DataFrame(columns=['profile pic','nums/length username','fullname words','nums/length fullname','name==username','description length','external URL','private','#posts','#followers','#follows'])
    dfObj = dfObj.append({'profile pic': final_features[0], 'nums/length username': final_features[1], 'fullname words': final_features[2],'nums/length fullname':final_features[3],'name==username':final_features[4],'description length':final_features[5],'external URL':final_features[6],'private':final_features[7],'#posts':final_features[8],'#followers':final_features[9],'#follows':final_features[10]  }, ignore_index=True)
    prediction = model.predict(dfObj)

    output = prediction
    res=""
    if output==0:
        res="Fake"
    else:
        res="Genuine"
    
    return 'This account should be {}'.format(res)

@app.route('/results',methods=['POST'])
def results():

    data = request.get_json(force=True)
    prediction = model.predict([np.array(list(data.values()))])

    output = prediction[0]
    return jsonify(output)

if __name__ == "__main__":
    app.run(debug=True)
