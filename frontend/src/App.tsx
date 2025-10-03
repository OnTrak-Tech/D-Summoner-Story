import { useState } from "react";

function App() {
  const [summonerName, setSummonerName] = useState("");
  const [region, setRegion] = useState("NA1");

  const onSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    // TODO: Wire to backend API Gateway endpoints
    console.log({ summonerName, region });
  };

  return (
    <div className="min-h-screen bg-gray-50 text-gray-900">
      <div className="max-w-xl mx-auto p-6">
        <h1 className="text-3xl font-bold mb-4">D-Summoner-Story</h1>
        <form onSubmit={onSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium">Summoner Name</label>
            <input
              className="mt-1 w-full border rounded p-2"
              value={summonerName}
              onChange={(e) => setSummonerName(e.target.value)}
              placeholder="Enter summoner name"
            />
          </div>
          <div>
            <label className="block text-sm font-medium">Region</label>
            <select
              className="mt-1 w-full border rounded p-2"
              value={region}
              onChange={(e) => setRegion(e.target.value)}
            >
              <option value="NA1">NA1</option>
              <option value="EUW1">EUW1</option>
              <option value="EUN1">EUN1</option>
              <option value="KR">KR</option>
              <option value="BR1">BR1</option>
              <option value="LA1">LA1</option>
              <option value="LA2">LA2</option>
              <option value="OC1">OC1</option>
              <option value="RU">RU</option>
              <option value="TR1">TR1</option>
              <option value="JP1">JP1</option>
            </select>
          </div>
          <button
            type="submit"
            className="w-full bg-indigo-600 text-white rounded py-2 hover:bg-indigo-700"
          >
            Get Year in Review
          </button>
        </form>
      </div>
    </div>
  );
}

export default App;
