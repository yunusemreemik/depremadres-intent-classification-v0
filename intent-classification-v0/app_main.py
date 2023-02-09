﻿from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn
import rule_based_clustering as rbc
#import pg_ops
import run_zsc as zsc
from tqdm import tqdm
import pandas as pd

app = FastAPI()

class Item(BaseModel):
    Full_text: str
    Tweet_id: str 
    Geo_loc: str
    Rules: list


@app.get("/")
def read_root():
    return {}


@app.post("/items/")
async def Get_Indent(item: Item):

    #Plotted indent rule data
    row = pd.DataFrame(item)
    plot_data = {"key": rbc.labels, "count": [0] * len(rbc.labels)}

    rule_based_labels, plot_data = rbc.process_tweet(row[0], plot_data)

    intent_results = ",".join(rule_based_labels) if rule_based_labels else ""
    
    #Check indent result
    if intent_results:

        zsc_result = zsc.query(
            {
                "inputs": row[1],
                "parameters": {"candidate_labels": rbc.labels},
            })

        if zsc_result is not None:
            # sequence, labels, scores
            if "scores" in zsc_result:
                
                label_scores = zsc_result["scores"]
                labels_filtered = [zsc_result["labels"][i] for i in range(len(label_scores)) if label_scores[i] > 0.3]
                intent_results = ",".join([label for label in labels_filtered])                
                plot_data = rbc.update_plot_data(plot_data, labels_filtered)

    return intent_results

if __name__ == '__main__':
    uvicorn.run(app, host="0.0.0.0", port=8000)


