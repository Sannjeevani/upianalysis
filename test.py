from bs4 import BeautifulSoup
import requests, json, lxml, re

# beautifulsoup, lxml to parse html
# requests to make requests to a website 
# re for regular expressions to help locate the parts of the html that we need where the data is located
# json to convert the parsed data from json to python dictionary + also for pretty printing

# NEXT:
# create user agent headers and search query parameters
# user agent headers are used to make it look like a real user visit from an actual browser so that our bot is not detected

headers = {
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36"
}
params = {
    "id": "com.kiloo.subwaysurf",     # app name
    "gl": "us",                    # country of the search
    "hl": "en_GB"                  # language of the search
}

# NEXT
# pass params and headers to a request

def google_store_app_data():
    html = requests.get("https://play.google.com/store/apps/details", params=params, headers=headers, timeout=30)
# the timeout argument tells the request to stop looking after 30s

# NEXT
# create a beautifulsoup object from the returned html
# by passing the HTML parser, which in this case is lxml

    soup = BeautifulSoup(html.text, "lxml")

# NEXT
# making a dictionary to store the extracted app data
    app_data = {
        "basic info" : {
            "developer" : {},
            "downloads info" : {}
        },
        "user comments" : []
    }

# matching basic and regular app info using regex bro
    basicAppInfo = json.loads(re.findall(r"<script nonce=\"\w+\" type=\"application/ld\+json\">({.*?)</script>", str(soup.select("script")[11]), re.DOTALL)[0])
# \w+ = word metacharacter, matches every word
# (.*?) is a regex group to capture everything
# the str argument tells soup to capture all the script tags, grab only [11] index from the script tags,
# and convert it all to string so the re module can use it
# re.dotall tells re to to match everything including newlines
# findall[0] will return first index from the returned list of matches
# json.loads() converts the parsed json to a python dictionary

    addnlBasicInfo = re.search(fr"<script nonce=\"\w+\">AF_initDataCallback\(.*?(\"{basicAppInfo.get('name')}\".*?)\);<\/script>", str(soup.select("script")), re.M|re.DOTALL).group(1)
# re.M mein M is alias for MULTILINE and it will match everything immediately following each newline

# now, we will access the json data from the dictionary wala var, i.e. basicAppInfo
    app_data["basic info"]["name"] = basicAppInfo.get("name")
    app_data["basic_info"]["type"] = basicAppInfo.get("@type")
    app_data["basic_info"]["url"] = basicAppInfo.get("url")
    app_data["basic_info"]["description"] = basicAppInfo.get("description").replace("\n", "")  # replace new line character to nothing
    app_data["basic_info"]["application_category"] = basicAppInfo.get("applicationCategory")
    app_data["basic_info"]["operating_system"] = basicAppInfo.get("operatingSystem")
    app_data["basic_info"]["thumbnail"] = basicAppInfo.get("image")
    app_data["basic_info"]["content_rating"] = basicAppInfo.get("contentRating")
    app_data["basic_info"]["rating"] = round(float(basicAppInfo.get("aggregateRating").get("ratingValue")), 1)  # 4.287856 -> 4.3
    app_data["basic_info"]["reviews"] = basicAppInfo.get("aggregateRating").get("ratingCount")
    app_data["basic_info"]["reviews"] = basicAppInfo.get("aggregateRating").get("ratingCount")
    app_data["basic_info"]["price"] = basicAppInfo["offers"][0]["price"]

    app_data["basic_info"]["developer"]["name"] = basicAppInfo.get("author").get("name")
    app_data["basic_info"]["developer"]["url"] = basicAppInfo.get("author").get("url")


# additonal info le liye same cheez
    app_data["basic_info"]["developer"]["email"] = re.search(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", addnlBasicInfo).group(0)

# https://regex101.com/r/Y2mWEX/1 (a few matches occures but re.search always matches the first occurence)
    app_data["basic_info"]["release_date"] = re.search(r"\d{1,2}\s[A-Z-a-z]{3}\s\d{4}", addnlBasicInfo).group(0)

# using different groups to extract different data
    app_data["basic_info"]["downloads_info"]["long_form_not_formatted"] = re.search(r"\"(\d+,?\d+,?\d+\+)\"\,(\d+),(\d+),\"(\d+M\+)\"", addnlBasicInfo).group(1)
    app_data["basic_info"]["downloads_info"]["long_form_formatted"] = re.search(r"\"(\d+,?\d+,?\d+\+)\"\,(\d+),(\d+),\"(\d+M\+)\"", addnlBasicInfo).group(2)
    app_data["basic_info"]["downloads_info"]["as_displayed_short_form"] = re.search(r"\"(\d+,?\d+,?\d+\+)\"\,(\d+),(\d+),\"(\d+M\+)\"", addnlBasicInfo).group(4)
    app_data["basic_info"]["downloads_info"]["actual_downloads"] = re.search(r"\"(\d+,?\d+,?\d+\+)\"\,(\d+),(\d+),\"(\d+M\+)\"", addnlBasicInfo).group(3)


    try:
        app_data["basic_info"]["video_trailer"] = "".join(re.findall(r"\"(https:\/\/play-games\.\w+\.com\/vp\/mp4\/\d+x\d+\/\S+\.mp4)\"", addnlBasicInfo)[0])
    except:
        app_data["basic_info"]["video_trailer"] = None

# EXTRACTING THE IMAGES FROM THE PAGE
# [2:] skips 2 PEGI logo thumbnails and extracts only app images 
    app_data["basic_info"]["images"] = re.findall(r",\[\d{3,4},\d{3,4}\],.*?(https.*?)\"", addnlBasicInfo)[2:]


# MATCHING USER COMMENTS with the regex
    user_reviews = re.findall(r'Write a short review.*?<script nonce="\w+">AF_initDataCallback\({key:.*data:\[\[\[\"\w.*?\",(.*?)sideChannel: {}}\);<\/script>', str(soup.select("script")), re.DOTALL)

# extracting all avatars, ratings and comments from user_reviews
# [::3] to grab every 2nd (second) picture to avoid duplicates
    avatars = re.findall(r",\"(https:.*?)\"\].*?\d{1}", str(user_reviews))[::3]

    ratings = re.findall(r"https:.*?\],(\d{1})", str(user_reviews))
# \d{1} to match exactly 1 digit number.

    comments = re.findall(r"https:.*?\],\d{1}.*?\"(.*?)\",\[\d+,\d+\]", str(user_reviews))

# adding this data to app_data
    for comment, rating, avatar in zip(comments, ratings, avatars):
        app_data["user_comments"].append({
            "user_avatar": avatar,
            "user_rating": rating,
            "user_comment": comment
        })

# app_user_comments = []
# app_user_comments.append({
#     "user_name": name,
#     "user_avatar": avatar,
#     "comment": comment,
#     "user_app_rating": user_app_rating,
#     "user__comment_likes": likes,
#     "user_comment_published_at": date,
#     "user_comment_id": comment_id
# })

    print(json.dumps(app_data, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    # https://stackoverflow.com/a/17533149/15164646
    # reruns script if `basic_app_info` or `additional_basic_info` throws an exception due to <script> position change
    while True: 
        try:
            google_store_app_data()
        except:
            pass
        else:
            break
# while loop was used to rerun the script if exception occurred. 
# In this case, the exception will be IndexError which appears from basic_app_info or additional_basic_info variables.

# This error occurs because on each page load, Google Play changes <script> elements position, 
# sometimes it's at index [11] (most often), sometimes at a different index. Rerunning the script fixes this problem for now.