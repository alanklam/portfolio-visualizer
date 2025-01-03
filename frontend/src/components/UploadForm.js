import React, { useState } from 'react';
import { useDropzone } from 'react-dropzone';

function UploadForm() {
  const [broker, setBroker] = useState('');
  const [file, setFile] = useState(null);

  const onDrop = (acceptedFiles) => {
    // Handle file drop
  };

  const { getRootProps, getInputProps, isDragActive } = useDropzone({ onDrop });

  const handleSubmit = async (e) => {
    e.preventDefault();
    // Handle form submission
  };

  return (
    <div className="upload-form">
      <h2>Upload Transaction File</h2>
      <form onSubmit={handleSubmit}>
        <select value={broker} onChange={(e) => setBroker(e.target.value)}>
          <option value="">Select Broker</option>
          <option value="fidelity">Fidelity</option>
          <option value="schwab">Charles Schwab</option>
          <option value="etrade">E-Trade</option>
        </select>

        <div {...getRootProps()} className="dropzone">
          <input {...getInputProps()} />
          {isDragActive ? (
            <p>Drop the files here ...</p>
          ) : (
            <p>Drag 'n' drop some files here, or click to select files</p>
          )}
        </div>

        <button type="submit">Upload</button>
      </form>
    </div>
  );
}

export default UploadForm; 