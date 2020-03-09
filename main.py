# Finding an apartment to rent software (Good name, I know)
import csv
import os
from urllib.request import urlopen as req
from bs4 import BeautifulSoup as soup
import googlemaps
import folium
import webbrowser, os

def html_parser(url):
    """ Open the web page, get the HTML and parse it """

    client = req(url)
    page_html = client.read()
    client.close()

    page_soup = soup(page_html, "html.parser")

    return page_soup


def scraper(posting_soup):
    """ Scrape all the important info from the HTML """

    indi_result = {}

    try:
        # Title
        title = posting_soup.findAll("h1", {"class": "title-2323565163"})
        title = title[0].string.strip()
        indi_result.update({"title": title})

        # Address
        address = posting_soup.findAll("span", {"class": "address-3617944557"})
        address = address[0].string.strip()
        indi_result.update({"address": address})

        # Price
        price = posting_soup.findAll("span", {"class": "currentPrice-2842943473"})[0].findChildren("span")[0]
        price = price.string.strip().replace("$", "")
        indi_result.update({"price": price})

        # Unit Type
        unit_type = posting_soup.find("dt", text='Unit Type')
        if unit_type == None:
            unit_type = posting_soup.findAll("span", {"class": "noLabelValue-3861810455"})[0].string.strip()

        else:
            unit_type = unit_type.findNext("dd").string.strip()
        indi_result.update({"unit_type": unit_type})

        # Bedrooms
        bedroom = posting_soup.find("dt", text='Bedrooms')
        if bedroom == None:
            bedroom = posting_soup.findAll("span", {"class": "noLabelValue-3861810455"})[1].string.strip().replace('Bedrooms: ', '')

        else:
            bedroom = bedroom.findNext("dd").string.strip()
        indi_result.update({"bedroom": bedroom})

        # Bathrooms
        bathroom = posting_soup.find("dt", text='Bathrooms')
        if bathroom == None:
            bathroom = posting_soup.findAll("span", {"class": "noLabelValue-3861810455"})[2].string.strip().replace('Bathrooms: ', '')

        else:
            bathroom = bathroom.findNext("dd").string.strip()
        indi_result.update({"bathroom": bathroom})

        # Size
        size = posting_soup.find("dt", text='Size (sqft)').findNext("dd").string.strip()
        indi_result.update({"size": size})

        # Hydro, Heat and Water
        utility_result = []

        utility_header = posting_soup.find("h4", text='Utilities Included')
        utility_list = utility_header.findNext("ul").findAll("li")

        try:
            for i in range(3):
                if len(utility_list[i]["class"]) == 2:
                    utility_result.append("Yes")

                else:
                    utility_result.append("No")

        except:
            utility_result.extend(['No', 'No', 'No'])

        indi_result.update({"hydro": utility_result[0], "heat": utility_result[1], "water": utility_result[2]})

    except:
        indi_result.update({"title": "None"})

    return indi_result


def write_excel(csv_file, indi_result, counter):
    """ Write data into Excel for storage """

    with open(csv_file, 'a') as file:
        writer = csv.writer(file, lineterminator='\n')
        if counter == 1:
            writer.writerow(
                ["TITLE", "ADDRESS", "PRICE", "UNIT TYPE", "BEDROOM", "BATHROOM", "SIZE", "HYDRO", "HEAT", "WATER",
                 "LINK", "LAT", "LNG"])

        writer.writerow(
            [indi_result["title"], indi_result["address"], indi_result["price"], indi_result["unit_type"], indi_result["bedroom"], indi_result["bathroom"],
             indi_result["size"], indi_result["hydro"], indi_result["heat"], indi_result["water"], indi_result["url"],
             indi_result["lat"], indi_result["lng"]])


def get_coordinate(address):
    """ Get the coordinates from each addresses """

    coordinates = []

    gmaps_key = googlemaps.Client(key="AIzaSyBCvit6y6I6ZbW7ozua7SPDtl_4WYnZcDU")
    geocode_result = gmaps_key.geocode(address)

    try:
        coordinates.append(geocode_result[0]["geometry"]["location"]["lat"])
        coordinates.append(geocode_result[0]["geometry"]["location"]["lng"])

    except:
        coordinates.append("None")
        coordinates.append("None")

    return coordinates


def visualize_map(visualize_data):
    """ Visualize data onto an interactive map """

    address = visualize_data[0]
    lat = visualize_data[1]
    lng = visualize_data[2]
    price = float(visualize_data[3].replace(",", ""))
    unit_type = visualize_data[4]
    url = str(visualize_data[5])

    # Create marker for my school
    folium.Marker(
        [45.3846817946, -75.6908639032],
        tooltip="Carleton University",
        icon=folium.Icon(icon="university", prefix='fas fa'),
    ).add_to(m)

    # Create markers for postings depending on prices
    popup_template = """
    <html>
        <body>
            <a href={} style="color: black; text-decoration: none !important" onMouseOver="this.style.color='#1E90FF'" onMouseOut="this.style.color='black'">
                <div style="font-size: 2rem; font-weight: bold; padding-bottom: 0.3rem">${:.2f}</div>
                <div style="font-size: 1.6rem; padding-bottom: 1rem">{}</div>
                <div style="font-size: 1.3rem">Unit Type: {}</div>
            </a>
        </body>
    </html>
    """.format(url, price, address, unit_type)

    if (price >= 1000) and (price < 1300):
        folium.Marker(
            [lat, lng],
            tooltip="${:.2f}".format(price),
            popup=folium.Popup(popup_template, max_width=200, min_width=200),
            icon=folium.Icon(icon="home", prefix='fas fa', color="pink"),
        ).add_to(m)

    elif (price >= 1300) and (price < 1700):
        folium.Marker(
            [lat, lng],
            tooltip="${:.2f}".format(price),
            popup=folium.Popup(popup_template, max_width=200, min_width=200),
            icon=folium.Icon(icon="home", prefix='fas fa', color="orange"),
        ).add_to(m)

    elif (price >= 1700) and (price <= 2000):
        folium.Marker(
            [lat, lng],
            tooltip="${:.2f}".format(price),
            popup=folium.Popup(popup_template, max_width=200, min_width=200),
            icon=folium.Icon(icon="home", prefix='fas fa', color="red"),
        ).add_to(m)


def main():
    """ Main function """

    # Get the parsed HTML
    links = []

    # Furnished or not
    furnished_input = input("Furnished (Yes/No): ")
    furnished_input = furnished_input.strip().lower()
    if furnished_input == "yes":
        furnished = 1

    elif furnished_input == "no":
        furnished = 0

    else:
        furnished = 0

    # How many pages?
    page_input = input("Number of pages scraped: ")
    page_input = int(page_input)

    for k in range(1, page_input):

        url = """https://www.kijiji.ca/b-apartments-condos/ottawa/1+bathroom__1+half+bathrooms-1+bedroom__1+bedroom+den__bachelor+studio-apartment__condo/page-{}/c37l1700185a120a27949001a29276001?furnished={}&price=1000__2000""".format(k, furnished)

        page_soup = html_parser(url)

        # Scrape, clean and store all the links of postings,
        raw_links = page_soup.findAll('a', {"class": "title"})

        for i in raw_links:

            i = i["href"].strip()

            if i not in links:
                links.append(i)


    # Delete CSV file if it exists
    if os.path.exists("rental.csv"):
        os.remove("rental.csv")

    # Scrape, clean and store the data for each posting
    result = []

    counter = 1

    # Create interactive map
    global m
    m = folium.Map(location=[45.424721, -75.695000], zoom_start=11)

   # Run through each posting individually
    for link in links:

        posting_url = 'https://www.kijiji.ca' + link
        posting_soup = html_parser(posting_url)

        # Prettify and write html to a HTML file
        pretty_html = posting_soup.prettify()
        with open('pretty_html.html', 'w', encoding='utf-8') as file:
           file.write(str(pretty_html))

        # Scrape the data
        indi_result = scraper(posting_soup)
        indi_result.update({"url": posting_url})

        if indi_result["title"] == "None":
            continue

        # Get coordinates based on address
        coordinates = get_coordinate(indi_result["address"])
        indi_result.update({"lat": coordinates[0], "lng": coordinates[1]})

        # Append each individual result into all results list
        result.append(indi_result)

        # Write data to Excel
        csv_file = "rental.csv"
        write_excel(csv_file, indi_result, counter)

        # Visualize data on an interactive map
        if (indi_result["lat"] != "None") and (indi_result["lng"] != "None"):
            visualize_data = [indi_result["address"], indi_result["lat"], indi_result["lng"], indi_result["price"],
                            indi_result["unit_type"], indi_result["url"]]

            visualize_map(visualize_data)

        print("Posting {} out of {} scraped.".format(counter, len(links)))

        counter += 1

    # Export map to HTML file
    m.save("map.html")

    # Open map in browser
    webbrowser.open('file://' + os.path.realpath("map.html"))

# Run the software
main()


