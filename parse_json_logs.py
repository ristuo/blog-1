import glob
import datetime
import re
import io
import jq
import gzip
import subprocess
import clfparser
import pandas as pd
import boto3
import os


def extract_article(s):
    if article_regex.match(s):
        return article_regex.search(s).group(3)


dirname = "logs-data"
os.makedirs(dirname, exist_ok=True)
dirs = glob.glob(dirname + "/*")
dates = [
    datetime.datetime.strptime(os.path.basename(x), "%Y-%m-%d").date() for x in dirs
]
newest_date = max(dates)
existing_files = glob.glob(dirname + "/**", recursive=True)

bucket = "wordpress-blog-1-logs"
s3_client = boto3.client("s3")
dates_in_s3 = []
years_response = s3_client.list_objects_v2(Bucket=bucket, Prefix="", Delimiter="/")
if "CommonPrefixes" in years_response:
    years_prefixes = years_response["CommonPrefixes"]
    for prefix in years_prefixes:
        months_response = s3_client.list_objects_v2(
            Bucket=bucket, Prefix=prefix["Prefix"], Delimiter="/"
        )
        months_prefixes = months_response["CommonPrefixes"]
        if "CommonPrefixes" in months_response:
            for prefix in months_response["CommonPrefixes"]:
                dates_response = s3_client.list_objects_v2(
                    Bucket=bucket, Prefix=prefix["Prefix"], Delimiter="/"
                )
                if "CommonPrefixes" in dates_response:
                    dates_in_s3 = [
                        datetime.datetime.strptime(x["Prefix"], "%Y/%m/%d/").date()
                        for x in dates_response["CommonPrefixes"]
                    ]
dates_to_process = [x for x in dates_in_s3 if x >= newest_date]

article_regex = re.compile('"([A-z]{3,6}) (/[0-9]{4}/[0-9]{2}/[0-9]{2})/(.*) .*"')
apache_log_regex = re.compile("^[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}")
for date in dates_to_process:
    os.makedirs(dirname + "/" + str(date), exist_ok=True)
    objects_response = s3_client.list_objects_v2(
        Bucket=bucket, Prefix=date.strftime("%Y/%m/%d")
    )
    if "Contents" in objects_response:
        objects = objects_response["Contents"]
        for o in objects:
            key = o["Key"]
            filename = os.path.basename(key)
            outpath = os.path.join(dirname, str(date), filename)
            if not os.path.exists(outpath):
                apache_logs = []
                bytes_in = io.BytesIO(
                    s3_client.get_object(Bucket=bucket, Key=key)["Body"].read()
                )
                string_in = gzip.GzipFile(fileobj=bytes_in).read().decode("utf-8")
                parsed_messages = jq.compile(".").input(text=string_in).all()
                for message in parsed_messages:
                    for log_event in message["logEvents"]:
                        if apache_log_regex.match(log_event["message"]):
                            parsed_log = clfparser.CLFParser.logDict(
                                log_event["message"]
                            )
                            apache_logs.append(parsed_log)
                if not len(apache_logs):
                    open(outpath, "a").close()
                    continue
                apache_logs = pd.DataFrame(apache_logs)
                apache_logs["article"] = apache_logs.r.apply(extract_article)
                read_events = apache_logs[apache_logs.article.notnull()]
                apache_logs.to_csv(outpath, index=False)

files = glob.glob(dirname + "/**", recursive=True)
files = [x for x in files if not os.path.isdir(x)]
rows = []
for f in files:
    if os.stat(f).st_size > 0:
        rows.append(pd.read_csv(f))
logs = pd.concat(rows)
logs["Useragent"] = logs.Useragent.str.lstrip('"').str.rstrip('"')
logs["r"] = logs.r.str.lstrip('"').str.rstrip('"')
logs["Referer"] = logs.Referer.str.lstrip('"').str.rstrip('"')
logs.to_csv("logs.csv")
