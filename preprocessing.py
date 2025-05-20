import os
import json
import pandas as pd
import re

def merge_csv_data(input_folder, output_csv):
    try:
        data_frames = []
        
        for root, subdirs, files in os.walk(input_folder):
            if "detail_attempt.csv" in files:
                file_path = os.path.join(root, "detail_attempt.csv")
                df = pd.read_csv(file_path, encoding="utf-8-sig")
                
                required_columns = ["sku", "name", "sale", "original_price", "sale_price", "colors", "sizes", "description", "url", "images"]
                df = df[required_columns]
                
                relative_path = os.path.relpath(root, input_folder)
                website_name = relative_path.split(os.sep)[0]  
                df.insert(0, "website", website_name) 
                
                df["path"] = file_path
                
                data_frames.append(df)
        
        if data_frames:
            merged_df = pd.concat(data_frames, ignore_index=True)
            merged_df.to_csv(output_csv, index=False, encoding="utf-8-sig")
            print(f"Dữ liệu đã được tổng hợp và lưu vào {output_csv}")
        else:
            print("Không tìm thấy file detail_attempt.csv nào trong thư mục dữ liệu.")
    except Exception as e:
        print(f"Lỗi: {e}")

def clean_and_process_data(input_csv, output_csv):
    df = pd.read_csv(input_csv)
    df = df.dropna(subset=['sku', 'name'], how='all')
    
    df['sku'] = df['sku'].astype(str).str.replace("SKU", "").str.strip()
    mask_sku_null = df["sku"].isna() | (df["sku"] == "") | (df["sku"].str.lower() == "nan")
    pattern = r"\b[A-Z]+\d+\b"
    
    def extract_sku(name):
        if pd.isna(name):
            return None
        match = re.search(pattern, name)
        return match.group(0) if match else None
    
    df.loc[mask_sku_null, "sku"] = df.loc[mask_sku_null, "name"].apply(extract_sku)
    
    def clean_name(name):
        if pd.isna(name):
            return name
        return re.sub(r"\b[A-Z]+\d+\b\s*-*\s*", "", name).strip()
    
    df["name"] = df["name"].apply(clean_name)
    
    df = df.drop_duplicates(subset=['sku', 'name'])
    
    df["sale"] = df["sale"].astype(str).str.replace("-", "").str.replace("%", "").replace("", "0").astype(float) / 100
    df["sale"] = df["sale"].fillna(0)
    
    df["original_price"] = df["original_price"].astype(str).apply(lambda x: re.sub(r'[^0-9]', '', x) if pd.notna(x) else "0").replace("", "0").astype(float)
    df["original_price"] = df["original_price"].fillna(0)
    
    if "sale_price" in df.columns:
        df["sale_price"] = df["sale_price"].astype(str).apply(lambda x: re.sub(r'[^0-9]', '', x) if pd.notna(x) else "0").replace("", "0").astype(float)
        df["sale_price"] = df["sale_price"].fillna(0)
    
    df.loc[(df["sale"] > 0) & (df["sale_price"] == 0), "sale_price"] = df["original_price"] - (df["original_price"] * df["sale"])
    df.loc[(df["sale_price"] > 0) & (df["sale"] == 0), "sale"] = (df["original_price"] - df["sale_price"]) / df["original_price"]
    
    df["sizes"] = df["sizes"].astype(str).str.replace(r"[\[\]']", "", regex=True).str.replace(",", "_").str.replace(" ", "")
    df["colors"] = df["colors"].astype(str).str.replace(r"[\[\]']", "", regex=True).str.replace(",", "_").str.replace("Màusắc:", "")
    df["description"] = df["description"].astype(str).str.replace(r"[\[\]']", "", regex=True).str.replace(",", "_")
    
    df.to_csv(output_csv, index=False)
    print(f"Dữ liệu đã được làm sạch và lưu vào {output_csv}")

if __name__ == "__main__":
    root_folder = "E:\\INTERN\\PORTFOLIO\\AUTOMATION\\SYSTEM\\data"
    raw_csv = "E:\\INTERN\\PORTFOLIO\\AUTOMATION\\SYSTEM\\merge_data.csv"
    clean_csv = "E:\\INTERN\\PORTFOLIO\\AUTOMATION\\SYSTEM\\clean_data.csv"
    
    merge_csv_data(root_folder, raw_csv)
    clean_and_process_data(raw_csv, clean_csv)