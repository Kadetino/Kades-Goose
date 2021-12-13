import pandas as pd

df = pd.read_csv('CSV bits\\data.csv')

def find_event(image_output):
    for event_index in range(len(df.index)):
        if(df['Event'][event_index] in image_output):
            return (df['Event'][event_index], df['Description'][event_index])
    return False