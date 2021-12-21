import pandas as pd

df = pd.read_csv('CSV bits\\data.csv')


def find_event(image_output):
    for event_index in range(len(df.index)):
        if df['Event'][event_index].lower() in image_output.lower():
            # Приведение к читабельному виду
            temp = df['Description'][event_index]
            temp = temp.replace("Option", "\n*Option")
            temp = temp.replace("Base mean time to happen", "\n*Base mean time to happen")
            temp = temp.replace("*****", "\n     ")
            temp = temp.replace("****", "\n   ")
            temp = temp.replace("***", "\n  ")
            temp = temp.replace("**", "\n ")
            temp = temp.replace("*", "\n")

            return df['Event'][event_index], temp
    return False
