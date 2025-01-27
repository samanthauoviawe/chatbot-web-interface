// app/page.tsx
"use client";  // This directive is necessary for the component to work on the client-side in Next.js 13+

import { useState, useRef, useEffect } from "react";
import axios from "axios";

// State Management:
export default function Home() {
  const [input, setInput] = useState(""); // Stores the current message the user is typing.
  const [messages, setMessages] = useState<{ text: string; type: string }[]>([]); // Holds an array of messages in the chat
  const [loading, setLoading] = useState(false);  // Boolean flag for loading state
  const [chatVisible, setChatVisible] = useState(false); // To toggle visibility of the chat window
  const messagesEndRef = useRef<HTMLDivElement>(null); // Reference for scrolling to the bottom

  // sendMessage Function:
  const sendMessage = async () => {
    if (!input.trim()) return; // Checks if input is not empty 
    setMessages((prevMessages) => [
      ...prevMessages, { text: input, type: "user" }]); // Adds the user's message to the messages array 
    setInput(""); // Clears the input field
    setLoading(true); // Set loading to true while waiting for response

    try {
      const res = await axios.post("http://localhost:8000/chat", { text: input }); // Sends the message via Axios Post request to the backend
      setMessages((prevMessages) => [
        ...prevMessages, { text: res.data.response, type: "bot" }]); // Adds the chatbot's response to the messages array
    } catch (error) {
      console.error("Error fetching chatbot response:", error);
      setMessages((prevMessages) => [
        ...prevMessages, { text: "Error: Could not reach the server.", type: "bot" }]); // Displays an error message
    } finally {
      setLoading(false);  // Set loading to false when the request completes (success or error)
    }
  };

  // Scroll to the bottom whenever new messages are added
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);  // Dependency array ensures it runs every time the messages change

  return (
    <div>
     {/* Welcome message */}
     <div className="flex flex-col items-center justify-center min-h-screen">
        <h1 className="text-4xl font-bold mb-4">Welcome to the Chatbot!</h1>
        <p className="text-lg mb-6">Start interacting with the bot below.</p>
      </div>
     
      {/* The button to toggle the chat window */}
      <button
        className="fixed bottom-4 right-4 inline-flex items-center justify-center text-sm font-medium disabled:pointer-events-none disabled:opacity-50 border rounded-full w-16 h-16 bg-black hover:bg-gray-700 m-0 cursor-pointer border-gray-200 bg-none p-0 normal-case leading-5 hover:text-gray-900"
        type="button"
        aria-haspopup="dialog"
        aria-expanded="false"
        data-state="closed"
        onClick={() => setChatVisible(!chatVisible)}  // Toggles the chat window visibility
      >
        <svg xmlns="http://www.w3.org/2000/svg" width="30" height="40" viewBox="0 0 24 24" fill="none"
          stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"
          className="text-white block border-gray-200 align-middle">
          <path d="m3 21 1.9-5.7a8.5 8.5 0 1 1 3.8 3.8z" className="border-gray-200"></path>
        </svg>
      </button>

      {/* Chatbox container, which is now conditionally visible */}
      {chatVisible && (
        <div style={{ boxShadow: "0 0 #0000, 0 0 #0000, 0 1px 2px 0 rgb(0 0 0 / 0.05)" }}
          className="fixed bottom-[calc(4rem+1.5rem)] right-0 mr-4 bg-white p-6 rounded-lg border border-[#e5e7eb] w-[440px] h-[634px]">

          {/* Heading */}
          <div className="flex flex-col space-y-1.5 pb-6">
            <h2 className="font-semibold text-lg tracking-tight">Chatbot</h2>
            <p className="text-sm text-[#6b7280] leading-3">Powered by Mendable and Vercel</p>
          </div>

          {/* Chat Container */}
          <div
            className="pr-4 h-[474px] overflow-y-auto" 
            style={{ minWidth: "100%", display: "flex", flexDirection: "column" }} // Reverted flex-direction to column to show messages from top to bottom
          >
            {/* Render chat messages */}
            {messages.map((msg, idx) => (
              <div key={idx} className="flex gap-3 my-4 text-gray-600 text-sm">
                <span className="relative flex shrink-0 overflow-hidden rounded-full w-8 h-8">
                  <div className="rounded-full bg-gray-100 border p-1">
                    <svg stroke="none" fill="black" strokeWidth="0" viewBox="0 0 16 16" height="20" width="20" xmlns="http://www.w3.org/2000/svg">
                      <path d="M8 8a3 3 0 1 0 0-6 3 3 0 0 0 0 6Zm2-3a2 2 0 1 1-4 0 2 2 0 0 1 4 0Zm4 8c0 1-1 1-1 1H3s-1 0-1-1 1-4 6-4 6 3 6 4Zm-1-.004c-.001-.246-.154-.986-.832-1.664C11.516 10.68 10.289 10 8 10c-2.29 0-3.516.68-4.168 1.332-.678.678-.83 1.418-.832 1.664h10Z"></path>
                    </svg>
                  </div>
                </span>
                <p className="leading-relaxed"><span className="block font-bold text-gray-700">{msg.type === 'user' ? 'You' : 'AI'}</span>{msg.text}</p>
              </div>
            ))}
            {/* Scroll to bottom */}
            <div ref={messagesEndRef} />
          </div>

          {/* Input box */}
          <div className="flex items-center pt-0">
            <form className="flex items-center justify-center w-full space-x-2">
              <input
                className="flex h-10 w-full rounded-md border border-[#e5e7eb] px-3 py-2 text-sm placeholder-[#6b7280] focus:outline-none focus:ring-2 focus:ring-[#9ca3af] disabled:cursor-not-allowed disabled:opacity-50 text-[#030712] focus-visible:ring-offset-2"
                placeholder="Type your message"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                disabled={loading} // Disable input while loading
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    sendMessage();  // Send message if Enter key is pressed
                  }
                }}
              />
              <button
                className="inline-flex items-center justify-center rounded-md text-sm font-medium text-[#f9fafb] disabled:pointer-events-none disabled:opacity-50 bg-black hover:bg-[#111827E6] h-10 px-4 py-2"
                type="button"
                onClick={sendMessage} // Sends message when clicked
                disabled={loading}  // Disable button while loading
              >
                {loading ? "Sending..." : "Send"}
              </button>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
