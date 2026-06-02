const socket = new WebSocket("ws://localhost:8080");

socket.onopen = () => {
  console.log("Connected to server");
};

socket.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log(data)
};

socket.onclose = () => {
  console.log("Disconnected");
};

socket.onerror = (err) => {
  console.error("Error:", err);
};