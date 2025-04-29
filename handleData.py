import pandas as pd
import json
###################
# temperature data is in csv type like folowing below
# Havaintoasema,"Year","Month","Day","Time","MedianTemp"
# Lappeenranta lentoasema,"2024","1","1","00:00","-14.1"
#
# Exchangeprice data is in json format example data below.
# {
#    "prices": [
#      {
#        "date": "2024-01-01T00:00:00.000Z",
#        "value": 3.529
#      }
# }
#
pricesFile = "exchangePrices.json"
tempFile = "temp.csv"
def prices(pricesFile=pricesFile,tempFile=tempFile):
    with open(pricesFile, "r") as f:
        price_data = json.load(f)

    # 2. Convert the list of prices to DataFrame
    price_df = pd.DataFrame(price_data["prices"])

    # 3. Convert the 'date' column to datetime and set as index
    price_df["date"] = pd.to_datetime(price_df["date"])
    price_df.set_index("date", inplace=True)

    price_df = price_df.tz_localize(None)

    # 4. Rename 'value' to "Price (c/kWh)"
    price_df.rename(columns={"value": "Price"}, inplace=True)

    # print(price_df.head())

    df = pd.read_csv(
        tempFile,
        sep=",",
        header=0,
        usecols=[1,2,3,4,5],
        decimal="."
        )
    df["Datetime"] = pd.to_datetime(
        df["Year"].astype(str) + "-" +
        df["Month"].astype(str).str.zfill(2) + "-" +
        df["Day"].astype(str).str.zfill(2) + " " +
        df["Time"]
    )
    df.set_index("Datetime",inplace=True)
    df.drop(columns=["Year","Month","Day","Time"],inplace=True)
    # print(df.head())

    merged_df = pd.merge(df,price_df,left_index=True,right_index=True,how="inner")
    merged_df.index.name = "Datetime"
    # for i in merged_df.itertuples():
    #     print(i.Index,i.Price,i.MedianTemp)

    # print(merged_df.index.name)
    return merged_df
