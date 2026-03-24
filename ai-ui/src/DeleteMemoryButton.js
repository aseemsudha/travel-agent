import React, { useState } from "react";

function DeleteMemoryButton({ sessionId }) {
  const [loading, setLoading] = useState(false);

  const handleDelete = async () => {
    const confirmDelete = window.confirm(
      "Are you sure you want to delete your memories?"
    );
    if (!confirmDelete) return;

    setLoading(true);

    try {
      const res = await fetch(`http://127.0.0.1:8000/api/memory?session_id=${sessionId}`, {
        method: "DELETE",
      });
      const data = await res.json();
      alert(data.message);
    } catch (err) {
      console.error(err);
      alert("Failed to delete memory");
    } finally {
      setLoading(false);
    }
  };

  return (
    <button
      onClick={handleDelete}
      disabled={loading}
      className={`px-4 py-2 rounded text-white ${
        loading ? "bg-gray-400 cursor-not-allowed" : "bg-red-500 hover:bg-red-600"
      }`}
    >
      {loading ? "Deleting..." : "Delete Memory"}
    </button>
  );
}

export default DeleteMemoryButton;