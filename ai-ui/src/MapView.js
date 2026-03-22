import React from "react";
import { GoogleMap, Marker, useJsApiLoader } from "@react-google-maps/api";

const containerStyle = {
  width: "100%",
  height: "300px"
};

function MapView({ places }) {
  const safePlaces = places || [];

  const { isLoaded } = useJsApiLoader({
    googleMapsApiKey: process.env.REACT_APP_GOOGLE_MAPS_API_KEY
  });

  const center = safePlaces.length
    ? { lat: safePlaces[0].lat, lng: safePlaces[0].lng }
    : { lat: 20.5937, lng: 78.9629 };

  const openInGoogleMaps = (lat, lng) => {
    window.open(`https://www.google.com/maps?q=${lat},${lng}`, "_blank");
  };

  if (!isLoaded) return <div>Loading map...</div>;

  return (
    <GoogleMap mapContainerStyle={containerStyle} center={center} zoom={10}>
      {safePlaces
        .filter((place) => place.lat && place.lng)
        .map((place, idx) => (
          <Marker
            key={idx}
            position={{ lat: place.lat, lng: place.lng }}
            title={place.name}
            onClick={() => openInGoogleMaps(place.lat, place.lng)}
          />
        ))}
    </GoogleMap>
  );
}

export default React.memo(MapView);