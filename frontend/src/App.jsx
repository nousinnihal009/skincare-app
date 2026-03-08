import { useState } from "react";
import axios from "axios";

function App() {
  const [file, setFile] = useState(null);
  const [result, setResult] = useState("");

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
  };

  const handleUpload = async () => {
    if (!file) return;

    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await axios.post("http://127.0.0.1:8000/predict", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      setResult(res.data.received_file);
    } catch (err) {
      console.error(err);
      setResult("Error uploading file");
    }
  };

  return (
    <div style={{ padding: 20 }}>
      <h1>SkinCare AI</h1>
      <input type="file" accept="image/*" onChange={handleFileChange} />
      <button onClick={handleUpload}>Upload</button>
      <p>Result: {result}</p>
    </div>
  );
}

export default App;