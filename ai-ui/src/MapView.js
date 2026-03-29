// import React from "react";
// import { GoogleMap, Marker, useJsApiLoader } from "@react-google-maps/api";

// const containerStyle = {
//   width: "100%",
//   height: "300px"
// };

// function MapView({ places }) {
//   const safePlaces = places || [];
    
//   const safePlaces = Array.isArray(places) ? places : [];

//   const { isLoaded } = useJsApiLoader({
//     googleMapsApiKey: process.env.REACT_APP_GOOGLE_MAPS_API_KEY
//   });

//   const center = safePlaces.length
//     ? { lat: safePlaces[0].lat, lng: safePlaces[0].lng }
//     : { lat: 20.5937, lng: 78.9629 };

//   const openInGoogleMaps = (lat, lng) => {
//     window.open(`https://www.google.com/maps?q=${lat},${lng}`, "_blank");
//   };

//   if (!isLoaded) return <div>Loading map...</div>;

//   return (
//     <GoogleMap mapContainerStyle={containerStyle} center={center} zoom={10}>
//       {safePlaces
//         .filter((place) => place.lat && place.lng)
//         .map((place, idx) => (
//           <Marker
//             key={idx}
//             position={{ lat: place.lat, lng: place.lng }}
//             title={place.name}
//             onClick={() => openInGoogleMaps(place.lat, place.lng)}
//           />
//         ))}
//     </GoogleMap>
//   );
// }

// export default React.memo(MapView);



import React, { useEffect, useState } from "react";
import { GoogleMap, Marker, useJsApiLoader } from "@react-google-maps/api";

const containerStyle = {
  width: "100%",
  height: "300px"
};

function MapView({ places }) {
  console.log("MapView received places:", places);
  // const safePlaces = places || [];
  const safePlaces = Array.isArray(places) ? places : [];

  console.log(
    "First place lat/lng types:",
    typeof safePlaces[0]?.lat,
    typeof safePlaces[0]?.lng
  );

  

  const { isLoaded } = useJsApiLoader({
    googleMapsApiKey: process.env.REACT_APP_GOOGLE_MAPS_API_KEY
  });

  const [mapCenter, setMapCenter] = useState({
    lat: 20.5937,
    lng: 78.9629
  });

  useEffect(() => {
    if (safePlaces.length) {
      console.log("Updating center to:", safePlaces[0]);

      setMapCenter({
        lat: safePlaces[0].lat,
        lng: safePlaces[0].lng
      });
    }
  }, [safePlaces]);

  const openInGoogleMaps = (lat, lng) => {
    window.open(`https://www.google.com/maps?q=${lat},${lng}`, "_blank");
  };

  if (!isLoaded) return <div>Loading map...</div>;

  return (
    <GoogleMap
      mapContainerStyle={containerStyle}
      center={mapCenter}
      zoom={10}
    >
      {safePlaces
        .filter((place) => place.lat && place.lng)
        .map((place, idx) => (
          <Marker
            key={idx}
            position={{
              lat: Number(place.lat),
              lng: Number(place.lng)
            }}
            title={place.name}
            onClick={() =>
              openInGoogleMaps(place.lat, place.lng)
            }
          />
        ))}
    </GoogleMap>
  );
}

export default React.memo(MapView);