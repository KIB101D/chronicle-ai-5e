// api.js
const API_URL = "http://127.0.0.1:8000/api/analyze";

export async function analyzeCharacterStory(storyText) {
  const response = await fetch(API_URL, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ story: storyText }),
  });

  if (!response.ok) {
    throw new Error(`HTTP error! Status: ${response.status}`);
  }

  return await response.json();
}
