from flask import request, jsonify
from config import app, db
from models import Dustbin
import aux_functions
import thingspeak, os
from flask import send_from_directory, Flask, send_file
hubLatitude = None
hubLongitude = None


@app.route("/")
def serve_frontend():
    return send_from_directory("../frontend", "index.html")

# Serve static assets
@app.route("/<path:path>")
def serve_static(path):
    return send_from_directory("../frontend", path)

@app.route("/plan_optimized_route", methods=["POST"])
def plan_optimized_route_handler():
    global hubLatitude, hubLongitude
    if hubLatitude is None or hubLongitude is None:
        return jsonify({"message": "Hub address not available"}), 400
    #print(f"Printing from plan_optimized_route_handler: {hubLatitude} and {hubLongitude}")
    dustbins_data = request.json.get("dustbins")
    dustbins = [(d.get('latitude'), d.get('longitude'), d.get('capacity')) for d in dustbins_data]
    optimized_route = aux_functions.plan_optimized_route(dustbins, hubLatitude, hubLongitude)
    
    """
        input change to 3 params : [lat(float), long(float), deadline(minutes/hours/int)]
        tom_tom_api call with
            input params : [lat, long, unit(kmph), openLR(static), key(secret key)]
            output : [flow_segment_data : {"free_flow_speed":"", "current_speed": ""}]
            
        current_speed:
        


    """

    
    return jsonify({"optimized_route": optimized_route}), 200

@app.route("/route_map")
def serve_route_map():
    return send_from_directory(directory='backend', path='route_map.html')
    

@app.route("/dustbins", methods=["GET"])
def get_dustbins():
    dustbins = Dustbin.query.all()
    json_dustbins = list(map(lambda x: x.to_json(), dustbins))
    return jsonify({"dustbins": json_dustbins})

@app.route("/create_hub", methods=["POST"])
def print_hub():
    global hubLatitude, hubLongitude
    hubLatitude=request.json.get("hubLatitude")
    hubLongitude=request.json.get("hubLongitude")
    print(f"the hubLatitiude is{hubLatitude} and hubLongitude is {hubLongitude}")
    if hubLatitude and hubLongitude:
        return jsonify({"message": "Hub Address committed"}), 201

@app.route("/create_dustbin", methods=["POST"])
def create_dustbin():
    address = request.json.get("address")
    latitude = request.json.get("latitude")
    longitude = request.json.get("longitude")
    capacity = request.json.get("capacity")

    if not latitude or not longitude or not capacity:
        return (
            jsonify({"message": "You must include the coordinates and capacity"}),
            400,
        )

    new_dustbin = Dustbin(address=address,latitude=latitude, longitude=longitude, capacity=capacity)
    try:
        db.session.add(new_dustbin)
        db.session.commit()
    except Exception as e:
        return jsonify({"message": str(e)}), 400

    return jsonify({"message": "Dustbin created!"}), 201


@app.route("/update_dustbin/<int:user_id>", methods=["PATCH"])
def update_dustbin(user_id):
    dustbin = session.get(Dustbin, user_id)

    if not dustbin:
        return jsonify({"message": "User not found"}), 404

    data = request.json
    dustbin.latitude = data.get("latitude", dustbin.latitude)
    dustbin.longitude = data.get("longitude", dustbin.longitude)
    dustbin.capacity = data.get("capacity", dustbin.capacity)

    db.session.commit()

    return jsonify({"message": "User updated."}), 200


@app.route("/delete_dustbin/<int:user_id>", methods=["DELETE"])
def delete_dustbin(user_id):
    dustbin = session.get(Dustbin, user_id)

    if not dustbin:
        return jsonify({"message": "Dustbin not found"}), 404

    db.session.delete(dustbin)
    db.session.commit()

    return jsonify({"message": "Dustbin deleted!"}), 200

def create_dustbin_from_thingspeak():
    latitude,longitude,capacity = thingspeak.dustbins()
    print(latitude)
    new_dustbin = Dustbin(latitude=latitude, longitude=longitude, capacity='12:30')
    try:
        db.session.add(new_dustbin)
        db.session.commit()
        print("commited Dustbin")
    except Exception as e:
        return jsonify({"message": str(e)}), 400

    print("control reaching here")
    return jsonify({"message": "Dustbin created!"}), 201

if __name__ == "__main__":
    with app.app_context():
        db.drop_all()
        db.create_all()
        print("Done 1")
        #create_dustbin_from_thingspeak()
        print("Done 2")
    
    app.run(debug=True)