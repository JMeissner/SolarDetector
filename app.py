import sys

from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QSplitter, QLabel, QPushButton, QHBoxLayout, QLineEdit
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QUrl
import requests
import geopy
import time

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Solar Detector")

        self.setGeometry(250, 250, 1600, 900)  # x, y, width, height

        # Create a central widget and a layout
        central_widget = QWidget()
        layout = QHBoxLayout()
        central_widget.setLayout(layout)

        # Create a QWebEngineView
        self.view = QWebEngineView()

        #create an inputfield
        self.adress_field = QLineEdit()

        # Load the Leaflet library and initialize the map
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <link rel="stylesheet" href="https://unpkg.com/leaflet@1.7.1/dist/leaflet.css" />
            <script src="https://unpkg.com/leaflet@1.7.1/dist/leaflet.js"></script>
        </head>
        <body>
            <div id="map" style="height: 95vh;"></div>
            <script>
                var map = L.map('map').setView([48.948792, 8.970334], 19);
                L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
                    attribution: 'Tiles &copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community',
                    maxZoom: 19
                }).addTo(map);

                function getViewportBounds() {
                    var bounds = map.getBounds();
                    return {
                        northEast: {
                            lat: bounds.getNorthEast().lat,
                            lng: bounds.getNorthEast().lng
                        },
                        southWest: {
                            lat: bounds.getSouthWest().lat,
                            lng: bounds.getSouthWest().lng
                        }
                    };
                }

                function jumpToCoordinates(lat, lng, zoom) {
                    // Check if the map object exists
                    if (typeof map !== 'undefined') {
                        // Create a new LatLng object with the specified coordinates
                        var newLocation = new L.LatLng(lat, lng);

                        // Pan the map to the new location
                        map.panTo(newLocation);

                        // Set the zoom level if provided
                        if (zoom) {
                            map.setZoom(zoom);
                        }
                    } else {
                        console.error("Map object is not defined.");
                    }
                }
            </script>
        </body>
        </html>
        """
        self.view.setHtml(html)

        # Connect a button click to get the viewport bounds
        # self.view.page().runJavaScript("getViewportBounds();", self.handle_viewport_bounds)

         # Create a sidebar widget
        self.sidebar = MainWindow.create_sidebar(self)

        # Add the QWebEngineView and the sidebar to the splitter
        layout.addWidget(self.view, 4)
        layout.addWidget(self.sidebar, 1)

        self.setCentralWidget(central_widget)

    def create_sidebar(self):
        sidebar = QWidget()
        sidebar.setStyleSheet("background-color: #f0f0f0;")

        layout = QVBoxLayout()

        header = QLabel("Solar Detector")
        # Apply stylesheets to set font size and make label bold
        header.setStyleSheet("""
            QLabel {
                font-size: 16px; /* Font size */
                font-weight: bold; /* Make the label bold */
            }
            """)
        adress_label = QLabel("Adress:")

        btn_jump_to_adress = QPushButton("Jump to Adress")
        btn_jump_to_adress.pressed.connect(lambda: self.jump_to_adress())

        btn_load_image = QPushButton("Load image")
        btn_load_image.pressed.connect(lambda: self.load_image())

        layout.addWidget(header)
        layout.addSpacing(14)
        layout.addWidget(adress_label)
        layout.addWidget(self.adress_field)
        layout.addWidget(btn_jump_to_adress)
        layout.addStretch()
        layout.addWidget(btn_load_image)
        sidebar.setLayout(layout)

        return sidebar
    
    def load_image(self):
        self.view.page().runJavaScript("getViewportBounds();", self.handle_viewport_bounds)
        return
    
    def jump_to_adress(self):
        coordinates = MainWindow.get_coordinates(self.adress_field.text())

        if coordinates:
            latitude, longitude = coordinates
            #print(f"Latitude: {latitude}, Longitude: {longitude}")
        else:
            print("Unable to retrieve coordinates for the given address.")
            return

        self.view.page().runJavaScript(f"jumpToCoordinates({latitude}, {longitude}, {19});")
        return

    def handle_viewport_bounds(self, result):
        # Azure Maps subscription key
        subscription_key = "Ap9-hl_U2JlIk9MNIe6dwta-lU2i7KaTqtQekLmjjX6cdKaIZ5IcLpHgAA_SBivp"

        # Extract the bounding box coordinates from the result variable
        west_longitude = result['southWest']['lng']
        south_latitude = result['southWest']['lat']
        east_longitude = result['northEast']['lng']
        north_latitude = result['northEast']['lat']

        # Construct the bounding box string
        bbox = f"{south_latitude},{west_longitude},{north_latitude},{east_longitude}"

        # Construct the URL for the Get Map Static request
        url = f"https://dev.virtualearth.net/REST/v1/Imagery/Map/Aerial?mapArea={bbox}&mapSize=1280,900&key={subscription_key}"

        # Send the GET request to the Azure Maps service
        response = requests.get(url)

        # Check if the request was successful
        if response.status_code == 200:
            # Save the map image to a file

            rnd = MainWindow.generate_5_digit_number()

            with open(f"images/map_{rnd}.jpg", "wb") as file:
                file.write(response.content)
            print("Map image saved successfully.")
        else:
            print(f"Error: {response.status_code} - {response.text}")
        #print(result)

    def get_coordinates(address):
        """
        Convert an address to latitude and longitude coordinates.

        Args:
            address (str): The address to be converted.

        Returns:
            tuple: A tuple containing the latitude and longitude as floats, or None if the address cannot be geocoded.
        """
        # Initialize the Nominatim geocoder
        geolocator = geopy.Nominatim(user_agent="solardetector")

        try:
            # Use the Nominatim geocoder to get the location
            location = geolocator.geocode(address)

            # If the location is found, return the latitude and longitude
            if location:
                latitude = location.latitude
                longitude = location.longitude
                return latitude, longitude
            else:
                print(f"Unable to geocode address: {address}")
                return None
        except geopy.exc.GeocoderTimedOut:
            print("Geocoder timed out. Please try again later.")
            return None
        
    def generate_5_digit_number():
        current_time = int(time.time()) # Get current time as a Unix timestamp
        random_5_digit_number = current_time % 100000  # Extract last 5 digits
        return random_5_digit_number

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())