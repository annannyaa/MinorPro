document.addEventListener('DOMContentLoaded', function () {
  document.getElementById('dustbinForm').addEventListener('submit', function (event) {
    event.preventDefault();
    submitDustbin();
  });

  document.getElementById('calculateRouteButton').addEventListener('click', function () {
    calculateOptimizedRoute();
  });

  loadDustbins();
});

async function submitDustbin() {
  var address = document.getElementById('address').value;
  var capacity = document.getElementById('capacity').value;

  // If address or capacity is not provided, show an alert
  if (!address || !capacity) {
    alert('Please fill in all fields.');
    return;
  }

  // Fetch latitude and longitude from Nominatim API based on the entered address
  try {
    const coordinates = await fetchCoordinatesFromAddress(address);

    if (coordinates) {
      var data = {
        address: address,
        latitude: coordinates.lat,
        longitude: coordinates.lon,
        capacity: capacity
      };

      // Send the dustbin data to the server
      const response = await fetch('http://127.0.0.1:5000/create_dustbin', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
      });

      // Check the response status
      if (response.status === 201) {
        alert('Drop-point added successfully!');
        loadDustbins();  // Refresh the dustbins list after creation
        clearFields();  // Clear the fields only after the dustbin is created
      } else {
        alert('Failed to add drop-point.');
      }
    } else {
      alert('Failed to get coordinates for the address.');
    }
  } catch (error) {
    console.error('An error occurred:', error);
    alert('An error occurred: ' + error);
  }
}

// Function to fetch coordinates using Nominatim API based on the address
function fetchCoordinatesFromAddress(address) {
  var url = `https://nominatim.openstreetmap.org/search?q=${encodeURIComponent(address)}&format=xml&polygon_kml=1&addressdetails=1`;

  return fetch(url)
    .then(response => response.text())
    .then(data => {
      var parser = new DOMParser();
      var xmlDoc = parser.parseFromString(data, "text/xml");
      var place = xmlDoc.getElementsByTagName('place')[0];

      if (place) {
        var lat = place.getAttribute('lat');
        var lon = place.getAttribute('lon');
        return { lat: lat, lon: lon };
      } else {
        return null;
      }
    })
    .catch(error => {
      console.error('Error fetching coordinates:', error);
      return null;
    });
}

function loadDustbins() {
  fetch('http://127.0.0.1:5000/dustbins')
    .then(function (response) {
      if (response.ok) {
        return response.json();
      } else {
        throw new Error('Failed to fetch dustbins.');
      }
    })
    .then(function (data) {
      var dustbinsContainer = document.getElementById('dustbinsContainer');
      dustbinsContainer.innerHTML = '';

      data.dustbins.forEach(function (dustbin) {
        var dustbinElement = document.createElement('div');
        dustbinElement.classList.add('dustbin');
        dustbinElement.innerHTML = `
          <p><strong>ID:</strong> ${dustbin.id}
          <strong>Address:</strong> ${dustbin.address}
          <strong>Latitude:</strong> ${dustbin.latitude}
          <strong>Longitude:</strong> ${dustbin.longitude}
          <strong>Deadline:</strong> ${dustbin.capacity}</p>
        `;
        dustbinsContainer.appendChild(dustbinElement);
      });
    })
    .catch(function (error) {
      alert('An error occurred: ' + error);
    });
}

function modifyDustbin(id) {
  var latitude = prompt('Enter new latitude:');
  var longitude = prompt('Enter new longitude:');
  var capacity = prompt('Enter new capacity:');

  if (latitude !== null && longitude !== null && capacity !== null) {
    var data = {
      latitude: latitude,
      longitude: longitude,
      capacity: capacity
    };

    fetch(`http://127.0.0.1:5000/update_dustbin/${id}`, {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(data)
    })
      .then(function (response) {
        if (response.ok) {
          alert('Dustbin modified successfully!');
          loadDustbins();
        } else {
          throw new Error('Failed to modify dustbin.');
        }
      })
      .catch(function (error) {
        alert('An error occurred: ' + error);
      });
  }
}

document.getElementById('checking').addEventListener('click', async function (event) {
  // Prevent form submission if the button is inside a form (optional if not using form)
  event.preventDefault();
  var hubAddress = document.getElementById('hub-address').value;
  var numRoutes = document.getElementById('numRoutes').value
  if (hubAddress) {
    console.log('Hub Address:', hubAddress);
    const hubLatLong = await fetchCoordinatesFromAddress(hubAddress);
    //   if (hubLatLong) {
    //     console.log('Hub Latitude:', hubLatLong.lat);
    //     console.log('Hub Longitude:', hubLatLong.lon);
    // } else {
    //     console.log('Coordinates not found.');
    // }
    var data = {
      hubLatitude: hubLatLong.lat,
      hubLongitude: hubLatLong.lon,
      numRoutes : numRoutes
    }
    const response = await fetch('http://127.0.0.1:5000/create_hub', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(data)
    });
    if (response.status === 201) {
      alert("Hub Address commited successfuly")
    }
    else {
      alert('Failed to commit HubAddress')
    }
  } else {
    alert('Please enter a valid address.');
  }
});


function calculateOptimizedRoute() {
  fetch('http://127.0.0.1:5000/dustbins')
    .then(function (response) {
      if (response.ok) {
        return response.json();
      } else {
        throw new Error('Failed to fetch dustbins.');
      }
    })
    .then(function (data) {
      var dustbins = data.dustbins;
      var dustbinsWithCoords = dustbins.filter(function (dustbin) {
        return dustbin.latitude && dustbin.longitude;
      });

      var dustbinsCoords = dustbinsWithCoords.map(function (dustbin) {
        return [parseFloat(dustbin.latitude), parseFloat(dustbin.longitude)];
      });

      var requestData = {
        dustbins: dustbinsWithCoords
      };

      // Fetch optimized route data
      return fetch('http://127.0.0.1:5000/plan_optimized_route', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(requestData)
      })
        .then(function (response) {
          if (response.ok) {
            return response.json();
          } else {
            throw new Error('Failed to calculate optimized route.');
          }
        })
        .then(function (data) {
          var optimizedRoutes = data.optimized_route;

          // Clear previous content
          document.getElementById('optimizedRouteSequence').innerHTML = '';

          // Loop through each optimized route and display it
          optimizedRoutes.forEach(function (optimizedRoute, routeIndex) {
            var optimizedRouteWithHub = ['Hub', ...optimizedRoute];
            var optimizedRouteSequence = optimizedRouteWithHub.join(' -> ');
            var routeElement = document.createElement('p');
            routeElement.textContent = `Route for cluster ${routeIndex + 1}: ${optimizedRouteSequence}`;
            document.getElementById('optimizedRouteSequence').appendChild(routeElement);
          });

          // Update the map iframe once after processing all routes
          const iframe = document.getElementById("mapContainer").querySelector("iframe");
          if (iframe) {
            iframe.src = "http://127.0.0.1:5501/backend/route_map.html";  // Always load the updated map with all routes
          }
        })
        .catch(function (error) {
          alert('An error occurred: ' + error);
        });
    })
    .catch(function (error) {
      alert('An error occurred: ' + error);
    });
}

function deleteDustbin(id) {
  if (confirm("Are you sure you want to delete this dustbin?")) {
    fetch(`http://127.0.0.1:5000/delete_dustbin/${id}`, {
      method: 'DELETE'
    })
      .then(function (response) {
        if (response.ok) {
          alert('Dustbin deleted successfully!');
          loadDustbins(); // Reload dustbins after deletion
        } else {
          throw new Error('Failed to delete dustbin.');
        }
      })
      .catch(function (error) {
        alert('An error occurred: ' + error);
      });
  }
}

function clearFields() {
  document.getElementById('address').value = '';
  document.getElementById('capacity').value = '';
}

var map = L.map('map').setView([13.04, 80.22], 12);

// Add OpenStreetMap tile layer to the map
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
  attribution: 'Map data © <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
}).addTo(map);

