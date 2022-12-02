import sys
import pandas as pd
import numpy as np
import argparse

# handle the arguments
parser = argparse.ArgumentParser(description="A test program.")
parser.add_argument("-i", "--input", help="Path to csv file.", type=str)
parser.add_argument("-o", "--output", help="Where to save output file.", type=str)
args = parser.parse_args()
if args.input is None or args.output is None:
    print("Please specify input and output paths -i --input, -o --output.")
    sys.exit(0)
if not args.input.endswith(".csv") and not args.input.endswith(".xlsx"):
    print("Input file should be .csv or .xlsx file.")
    sys.exit(0)

input_path = args.input
output_path = args.output

# read data
try:
    df = pd.read_excel(input_path)
except FileNotFoundError as e:
    print(f"File not found!", file=sys.stderr)
    sys.exit(0)
df["date"] = pd.to_datetime(
    dict(year=df["year"], month=df["month"], day=df["day"], seconds=df["sec_of_day"])
)
df["cumulative_secs"] = (df["date"] - df.iloc[0]["date"]).dt.total_seconds()
cols = [
    "cumulative_secs",
    "proton_density",
    "bulk_speed",
    "ion_temp",
    "bz",
    "bt",
    "longitude",
    "kp_index"
]
df = df[cols]

# filter out errors
df.loc[df["proton_density"] < 0, "proton_density"] = np.nan
df.loc[df["bulk_speed"] < 0, "bulk_speed"] = np.nan
df.loc[df["ion_temp"] < 0, "ion_temp"] = np.nan
df.loc[df["bt"] < 0, "bt"] = np.nan
df.loc[df["longitude"] < 0, "longitude"] = np.nan
df.loc[df["bz"] < -200, "bz"] = np.nan

# linear interpolate
df.interpolate(method="linear", inplace=True)

# 5 minutes average
df_res = df.rolling(5, min_periods=1, step=5).mean()
df_res["cumulative_secs"] = (df["cumulative_secs"].rolling(5, min_periods=1, step=5).max())
df_res["kp_index"] = (df["kp_index"].rolling(5, min_periods=1, step=5).min())
df_res.reset_index(drop=True, inplace=True)

# rename columns to names expected by the notebook
df_res.rename(columns={'bulk_speed':'speed', 'longitude':'phi_angle'}, inplace=True)

# save file
df_res.to_csv(output_path, index=False)
