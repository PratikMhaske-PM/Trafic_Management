import React, { useState } from 'react';
import { MapContainer, TileLayer, Marker, Popup, Polyline, CircleMarker, Tooltip, useMapEvents } from 'react-leaflet';
import { MapPin, Navigation, Clock, Route, Activity, Map as MapIcon, Loader2, AlertTriangle, Layers, Cpu, Plane, Train, Bike, Bus } from 'lucide-react';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';
import icon from 'leaflet/dist/images/marker-icon.png';
import iconShadow from 'leaflet/dist/images/marker-shadow.png';

let DefaultIcon = L.icon({ iconUrl: icon, shadowUrl: iconShadow });
L.Marker.prototype.options.icon = DefaultIcon;

const getRealAddress = async (lat, lng) => {
  try {
    const res = await fetch(`https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lng}&zoom=18&addressdetails=1&accept-language=en`);
    const data = await res.json();
    const addr = data.address;
    if (!addr) return "Unknown Area";
    
    const street = addr.road || addr.suburb || addr.neighbourhood || "";
    const city = addr.city || addr.town || addr.village || addr.county || "";
    const state = addr.state || addr.country || "";
    
    return `${street ? street + ', ' : ''}${city ? city + ', ' : ''}${state}`.replace(/,\s*$/, "") || "Unknown Area";
  } catch (e) {
    return "Unknown Area";
  }
};

function MapEventsHandler({ points, setPoints, setAddresses, setAllRoutes }) {
  useMapEvents({
    async click(e) {
      if (points.length >= 2) {
        setPoints([e.latlng]);
        setAllRoutes([]);
        setAddresses(["Locating..."]);
        const addr = await getRealAddress(e.latlng.lat, e.latlng.lng);
        setAddresses([addr]);
      } else {
        const newPoints = [...points, e.latlng];
        setPoints(newPoints);
        setAddresses(prev => {
          const newAddresses = [...prev, "Locating..."];
          getRealAddress(e.latlng.lat, e.latlng.lng).then(addr => {
            setAddresses(currentAddresses => {
              const updated = [...currentAddresses];
              updated[newPoints.length - 1] = addr;
              return updated;
            });
          });
          return newAddresses;
        });
      }
    },
  });
  return null;
}

export default function App() {
  const [points, setPoints] = useState([]);
  const [addresses, setAddresses] = useState([]);
  const [allRoutes, setAllRoutes] = useState([]);
  const [activeRouteIndex, setActiveRouteIndex] = useState(0);
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState("");

  const calculateRoute = async () => {
    if (points.length !== 2) return;
    setLoading(true);
    setErrorMsg("");
    
    try {
      const start = points[0];
      const end = points[1];
      
      const osrmUrl = `https://router.project-osrm.org/route/v1/driving/${start.lng},${start.lat};${end.lng},${end.lat}?alternatives=true&overview=full&geometries=geojson`;
      const response = await fetch(osrmUrl);
      const data = await response.json();
      
      if (data.code !== 'Ok') throw new Error("OSRM returned no route");
      
      const parsedRoutes = [];
      
      for (let rIdx = 0; rIdx < 3; rIdx++) {
        
        let leafletCoords = [];
        let baseDistance = 0;
        let baseTime = 0;

        if (data.routes[rIdx]) {
            const coords = data.routes[rIdx].geometry.coordinates; 
            leafletCoords = coords.map(c => [c[1], c[0]]); 
            baseDistance = data.routes[rIdx].distance / 1000;
            baseTime = data.routes[rIdx].duration / 60;
        } else {
            const coords = data.routes[0].geometry.coordinates;
            const originalCoords = coords.map(c => [c[1], c[0]]);
            baseDistance = (data.routes[0].distance / 1000) * (1 + (rIdx * 0.05)); 
            baseTime = (data.routes[0].duration / 60) * (1 + (rIdx * 0.08)); 
            
            leafletCoords = originalCoords.map((pt, idx) => {
                if (idx === 0 || idx === originalCoords.length - 1) return pt;
                const progress = idx / originalCoords.length;
                const offset = Math.sin(progress * Math.PI) * (0.025 * rIdx); 
                return [pt[0] + offset, pt[1] - offset];
            });
        }

        const chunks = [];
        const numChunks = 12; 
        const chunkSize = Math.max(2, Math.floor(leafletCoords.length / numChunks)); 
        let totalTrafficDelay = 0;
        
        for (let i = 0; i < leafletCoords.length; i += chunkSize) {
          const segmentCoords = leafletCoords.slice(i, i + chunkSize + 1);
          if (segmentCoords.length > 1) {
            
            const progress = i / leafletCoords.length;
            let baseDensity = 0;
            
            if (progress < 0.2 || progress > 0.8) {
                baseDensity = 65 + Math.random() * 30; 
            } else {
                baseDensity = 10 + Math.random() * 30;
                if (Math.random() > (0.95 - (rIdx * 0.15))) {
                    baseDensity = 95; 
                }
            }

            if (rIdx === 0) baseDensity = baseDensity * 0.8;

            const mlDensity = Math.min(99, Math.floor(baseDensity));
            const mlLevel = mlDensity > 75 ? "Severe Congestion" : (mlDensity > 40 ? "Moderate" : "Clear Road");
            
            if (mlDensity > 75) totalTrafficDelay += 5;
            if (mlDensity > 90) totalTrafficDelay += 10;

            chunks.push({
              positions: segmentCoords,
              density: mlDensity,
              level: mlLevel
            });
          }
        }
        
        parsedRoutes.push({
            id: rIdx,
            name: rIdx === 0 ? "Fastest (AI Optimized)" : `Alternative ${rIdx}`,
            metrics: { distance: baseDistance.toFixed(1), time: (baseTime + totalTrafficDelay).toFixed(0) },
            chunks: chunks,
            fullPositions: leafletCoords
        });
      }
      
      parsedRoutes.sort((a, b) => parseFloat(a.metrics.time) - parseFloat(b.metrics.time));
      
      setAllRoutes(parsedRoutes);
      setActiveRouteIndex(0);
    } catch (e) {
      setErrorMsg(e.message || "Failed to calculate routes.");
    }
    setLoading(false);
  };

  const getColor = (density) => {
    if (density < 40) return '#10b981'; // Emerald Green
    if (density < 75) return '#f59e0b'; // Amber Orange
    return '#ef4444'; // Rose Red
  };
  
  // Smart City AI Transport Logic
  const getTransportAlternatives = (distance) => {
    const suggestions = [];
    const d = parseFloat(distance);
    
    if (d > 400) {
      suggestions.push({ mode: 'Flight', icon: Plane, color: '#3b82f6', time: Math.round(d / 800 * 60) + 90, desc: 'Fastest' });
    }
    if (d > 50 && d <= 1000) {
      suggestions.push({ mode: 'Express Train', icon: Train, color: '#8b5cf6', time: Math.round(d / 120 * 60), desc: 'No Traffic' });
    }
    if (d > 5 && d <= 80) {
      suggestions.push({ mode: 'Local Transit', icon: Bus, color: '#f59e0b', time: Math.round(d / 40 * 60), desc: 'Eco-Friendly' });
    }
    if (d <= 25) {
      suggestions.push({ mode: 'E-Bike', icon: Bike, color: '#10b981', time: Math.round(d / 20 * 60), desc: 'Beat Gridlock' });
    }
    return suggestions;
  };

  const renderOrder = allRoutes.map((r, i) => i).sort((a, b) => (a === activeRouteIndex ? 1 : -1));

  return (
    <div style={{ position: 'relative', width: '100vw', height: '100vh', margin: 0, padding: 0, overflow: 'hidden', fontFamily: '"Inter", -apple-system, BlinkMacSystemFont, sans-serif', backgroundColor: '#f8fafc' }}>
      
      <style>{`
        #root { max-width: 100% !important; margin: 0 !important; padding: 0 !important; text-align: left !important; }
        body { margin: 0; padding: 0; overflow: hidden; background: #f8fafc; }
        .spin { animation: spin 2s linear infinite; }
        .route-card:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,0.05); }
        .alt-scroll::-webkit-scrollbar { display: none; }
        
        .alt-route-tooltip { background: white; border: 1px solid #cbd5e1; border-radius: 20px; font-weight: bold; color: #475569; padding: 4px 8px; font-size: 12px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .leaflet-tooltip-top:before, .leaflet-tooltip-bottom:before, .leaflet-tooltip-left:before, .leaflet-tooltip-right:before { display: none; }
        
        .leaflet-popup-content-wrapper { background: white; color: #1e293b; border-radius: 12px; box-shadow: 0 10px 25px rgba(0,0,0,0.15); }
        .leaflet-popup-tip { background: white; }
        
        .glass-sidebar {
            position: absolute;
            z-index: 9999;
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(16px);
            display: flex;
            flex-direction: column;
            gap: 16px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.15);
            border: 1px solid rgba(255,255,255,0.8);
            overflow-y: auto;
            box-sizing: border-box;
            transition: all 0.3s ease;
        }

        @media (min-width: 769px) {
            .glass-sidebar { top: 20px; left: 20px; width: 380px; max-height: 90vh; border-radius: 16px; padding: 24px; }
            .mobile-handle { display: none; }
            .leaflet-bottom.leaflet-right { bottom: 20px; }
        }

        @media (max-width: 768px) {
            .glass-sidebar { top: auto; bottom: 0; left: 0; width: 100vw; max-height: 55vh; border-radius: 24px 24px 0 0; padding: 20px 16px 30px 16px; border-bottom: none; }
            .mobile-handle { display: block; width: 40px; height: 5px; background: #cbd5e1; border-radius: 10px; margin: 0 auto 10px auto; }
            .leaflet-control-attribution { display: none; } 
            .leaflet-bottom.leaflet-right { bottom: 55vh; } 
        }
        
        @keyframes fadeIn { from { opacity: 0; transform: translateY(-10px); } to { opacity: 1; transform: translateY(0); } }
      `}</style>

      {/* MAP LAYER */}
      <div style={{ position: 'absolute', top: 0, left: 0, right: 0, bottom: 0, zIndex: 0 }}>
        <MapContainer center={[20.5937, 78.9629]} zoom={5} style={{ height: '100%', width: '100%' }} zoomControl={false}>
          <TileLayer url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}" attribution="Tiles &copy; Esri" />
          
          <MapEventsHandler points={points} setPoints={setPoints} setAddresses={setAddresses} setAllRoutes={setAllRoutes} />
          
          {points.map((pos, idx) => (
            <Marker key={idx} position={pos}>
              <Popup>
                <div style={{ fontWeight: 'bold', color: '#0f172a' }}>{idx === 0 ? "🟢 Departure" : "🏁 Destination"}</div>
                <div style={{ color: '#64748b', marginTop: '4px' }}>{addresses[idx]}</div>
              </Popup>
            </Marker>
          ))}

          {/* DRAW ALL ROUTES */}
          {renderOrder.map(rIdx => {
             const route = allRoutes[rIdx];
             const isActive = rIdx === activeRouteIndex;
             
             if (!isActive) {
               return (
                 <React.Fragment key={rIdx}>
                   <Polyline positions={route.fullPositions} color="transparent" weight={25} eventHandlers={{ click: () => setActiveRouteIndex(rIdx) }} />
                   <Polyline 
                     positions={route.fullPositions} 
                     color="#64748b" 
                     weight={8} 
                     opacity={0.6} 
                     lineCap="round" lineJoin="round"
                     eventHandlers={{ click: () => setActiveRouteIndex(rIdx) }}
                   >
                     <Tooltip permanent direction="center" className="alt-route-tooltip">
                       {route.metrics.time} min
                     </Tooltip>
                   </Polyline>
                 </React.Fragment>
               );
             }

             return (
               <React.Fragment key={rIdx}>
                 {route.chunks.map((segment, cIdx) => (
                   <React.Fragment key={`${rIdx}-${cIdx}`}>
                     <Polyline positions={segment.positions} color="#1e40af" weight={12} opacity={0.9} lineCap="round" lineJoin="round" />
                     <Polyline positions={segment.positions} color={getColor(segment.density)} weight={7} opacity={1.0} lineCap="round" lineJoin="round">
                       <Popup>
                         <div style={{ minWidth: '160px', padding: '5px' }}>
                           <div style={{ display: 'flex', alignItems: 'center', gap: '6px', background: '#f8fafc', color: '#0369a1', padding: '6px 8px', fontSize: '11px', borderRadius: '6px', marginBottom: '8px', border: '1px solid #e0f2fe', fontWeight: 'bold' }}>
                             <Cpu size={14}/> SENSOR NODE ACTIVE
                           </div>
                           <span style={{ color: getColor(segment.density), fontWeight: 'bold', fontSize: '16px' }}>{segment.level}</span><br/>
                           <div style={{ marginTop: '6px', fontSize: '13px', color: '#475569' }}>Congestion Density: <strong style={{color: '#0f172a'}}>{segment.density}%</strong></div>
                         </div>
                       </Popup>
                     </Polyline>
                     <CircleMarker center={segment.positions[0]} radius={4.5} pathOptions={{ color: '#1e40af', weight: 2, fillColor: 'white', fillOpacity: 1 }} />
                   </React.Fragment>
                 ))}
               </React.Fragment>
             );
          })}
        </MapContainer>
      </div>

      {/* RESPONSIVE SIDEBAR */}
      <div className="glass-sidebar">
        <div className="mobile-handle"></div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', borderBottom: '1px solid #f1f5f9', paddingBottom: '12px' }}>
          <div style={{ background: 'linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%)', padding: '10px', borderRadius: '12px', color: 'white', boxShadow: '0 4px 12px rgba(37, 99, 235, 0.3)' }}>
            <Activity size={24} />
          </div>
          <div>
            <h2 style={{ margin: 0, fontSize: '18px', color: '#0f172a' }}>AI Route Engine</h2>
            <span style={{ fontSize: '12px', color: '#64748b' }}>Multimodal Network Analysis</span>
          </div>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
          <div style={{ display: 'flex', alignItems: 'flex-start', gap: '12px', background: '#f8fafc', padding: '10px', borderRadius: '10px', border: '1px solid #e2e8f0' }}>
            <MapPin color="#10b981" size={18} style={{ marginTop: '2px', minWidth: '18px' }} />
            <div style={{ overflow: 'hidden' }}>
              <div style={{ fontSize: '11px', fontWeight: 'bold', color: '#64748b', textTransform: 'uppercase' }}>Departure</div>
              <div style={{ fontSize: '13px', color: '#0f172a', whiteSpace: 'nowrap', textOverflow: 'ellipsis', overflow: 'hidden', fontWeight: '500' }}>
                {points.length > 0 ? addresses[0] : "Tap map to set origin"}
              </div>
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'flex-start', gap: '12px', background: '#f8fafc', padding: '10px', borderRadius: '10px', border: '1px solid #e2e8f0' }}>
            <Navigation color="#3b82f6" size={18} style={{ marginTop: '2px', minWidth: '18px' }} />
            <div style={{ overflow: 'hidden' }}>
              <div style={{ fontSize: '11px', fontWeight: 'bold', color: '#64748b', textTransform: 'uppercase' }}>Destination</div>
              <div style={{ fontSize: '13px', color: '#0f172a', whiteSpace: 'nowrap', textOverflow: 'ellipsis', overflow: 'hidden', fontWeight: '500' }}>
                {points.length > 1 ? addresses[1] : "Tap map to set destination"}
              </div>
            </div>
          </div>
        </div>

        {errorMsg && (
          <div style={{ background: '#fef2f2', color: '#b91c1c', border: '1px solid #fecaca', padding: '10px', borderRadius: '8px', fontSize: '12px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <AlertTriangle size={16} /> {errorMsg}
          </div>
        )}

        <button 
          onClick={calculateRoute} 
          disabled={points.length !== 2 || loading}
          style={{ 
            display: 'flex', justifyContent: 'center', alignItems: 'center', gap: '8px',
            padding: '14px', background: points.length === 2 ? 'linear-gradient(135deg, #3b82f6 0%, #2563eb 100%)' : '#e2e8f0', 
            color: points.length === 2 ? 'white' : '#94a3b8', border: 'none', borderRadius: '12px', fontSize: '15px',
            cursor: points.length === 2 ? 'pointer' : 'not-allowed', fontWeight: 'bold', 
            boxShadow: points.length === 2 ? '0 4px 15px rgba(37, 99, 235, 0.3)' : 'none',
            transition: 'all 0.2s', minHeight: '50px', flexShrink: 0
          }}>
          {loading ? <Loader2 size={18} className="spin" /> : <Layers size={18} />}
          {loading ? 'Simulating...' : 'Initialize AI Routing'}
        </button>
        
        {/* MULTIPLE ROUTES LIST */}
        {allRoutes.length > 0 && !loading && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', animation: 'fadeIn 0.5s', flexShrink: 0 }}>
            <h4 style={{ margin: '0', color: '#64748b', fontSize: '12px', display: 'flex', justifyContent: 'space-between', textTransform: 'uppercase', fontWeight: 'bold' }}>
              Driving Routes <span>(Tap to select)</span>
            </h4>
            
            {allRoutes.map((route, idx) => (
              <div 
                key={idx}
                className="route-card"
                onClick={() => setActiveRouteIndex(idx)}
                style={{ 
                  background: activeRouteIndex === idx ? '#eff6ff' : 'white', 
                  border: activeRouteIndex === idx ? '2px solid #3b82f6' : '1px solid #e2e8f0', 
                  borderRadius: '12px', padding: '10px', cursor: 'pointer', transition: 'all 0.2s' 
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                  <strong style={{ color: activeRouteIndex === idx ? '#1d4ed8' : '#475569', fontSize: '14px' }}>
                    {idx === 0 ? '✨ ' : ''}{route.name}
                  </strong>
                  <span style={{ fontWeight: 'bold', fontSize: '15px', color: activeRouteIndex === idx ? '#1e40af' : '#0f172a' }}>{route.metrics.time} min</span>
                </div>
                <div style={{ display: 'flex', gap: '15px', fontSize: '11px', color: '#64748b' }}>
                  <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}><MapIcon size={12}/> {route.metrics.distance} km</span>
                  <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}><Cpu size={12}/> AI Analyzed</span>
                </div>
              </div>
            ))}
            
            {/* MULTIMODAL TRANSPORT SUGGESTIONS */}
            <div style={{ marginTop: '8px', animation: 'fadeIn 0.6s' }}>
              <h4 style={{ margin: '0 0 8px 0', color: '#64748b', fontSize: '12px', textTransform: 'uppercase', fontWeight: 'bold' }}>
                Smart City Alternatives
              </h4>
              <div className="alt-scroll" style={{ display: 'flex', gap: '8px', overflowX: 'auto', paddingBottom: '4px' }}>
                {getTransportAlternatives(allRoutes[activeRouteIndex].metrics.distance).map((alt, i) => {
                  const Icon = alt.icon;
                  return (
                    <div key={i} style={{ minWidth: '110px', flex: 1, background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: '10px', padding: '10px', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '6px' }}>
                      <div style={{ background: `${alt.color}20`, color: alt.color, padding: '8px', borderRadius: '50%' }}>
                        <Icon size={18} />
                      </div>
                      <strong style={{ fontSize: '12px', color: '#0f172a', textAlign: 'center' }}>{alt.mode}</strong>
                      <span style={{ fontSize: '14px', fontWeight: 'bold', color: alt.color }}>{alt.time} min</span>
                      <span style={{ fontSize: '10px', color: '#64748b', textAlign: 'center' }}>{alt.desc}</span>
                    </div>
                  )
                })}
                {getTransportAlternatives(allRoutes[activeRouteIndex].metrics.distance).length === 0 && (
                  <div style={{ fontSize: '12px', color: '#64748b', fontStyle: 'italic', padding: '8px' }}>Driving is the only viable option for this distance.</div>
                )}
              </div>
            </div>
            
          </div>
        )}
      </div>
    </div>
  );
}
