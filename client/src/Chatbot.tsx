import "regenerator-runtime/runtime";
import { useState, useEffect } from "react";
import { TbHelpHexagonFilled } from "react-icons/tb";
import {
  GoAlertFill,
  GoCheckCircleFill,
  GoCodeSquare,
  GoGitPullRequest,
  GoFlame,
} from "react-icons/go";
import { FaMicrophoneAlt, FaStopCircle, FaStop } from "react-icons/fa";
import { GrSend } from "react-icons/gr";
import { motion } from "framer-motion";
import SpeechRecognition, {
  useSpeechRecognition,
} from "react-speech-recognition";
import { Typewriter } from "react-simple-typewriter";
import Markdown from "react-markdown";

function AiCard({
  Icon,
  title,
  text,
}: {
  Icon: any;
  title: string;
  text: string;
}) {
  return (
    <div className="bg-white rounded-md border p-4 sm:p-3 hover:ring-1 hover:ring-slate-300 cursor-pointer transition-all">
      <Icon className="w-10 h-10 opacity-70 mb-4 text-fill sm:w-8 sm:h-8" />
      <h1 className="font-bold text-xl text-primary sm:text-lg">{title}</h1>
      <p className="text-sm opacity-95 sm:text-xs">{text}</p>
    </div>
  );
}

function speak(text: string) {
  const utterance = new SpeechSynthesisUtterance(text);
  const voices = speechSynthesis.getVoices();
  utterance.voice = voices[0];
  speechSynthesis.speak(utterance);
}

function chatbot() {
  const [messages, setMessages] = useState<any[]>([]);
  const [prompt, setPrompt] = useState<string>("");
  const [isListening, setIsListening] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [abortController, setAbortController] =
    useState<AbortController | null>(null);

  const {
    finalTranscript,
    resetTranscript,
    listening,
    browserSupportsSpeechRecognition,
  } = useSpeechRecognition();

  if (!browserSupportsSpeechRecognition) {
    alert("Browser doesn't support speech recognition.");
  }

  useEffect(() => {
    if (finalTranscript !== "") {
      handleSendMessage(finalTranscript);
      setIsListening(false);
    }
  }, [finalTranscript]);

  const handleMicClick = () => {
    if (isListening) {
      SpeechRecognition.stopListening();
    } else {
      resetTranscript();
      SpeechRecognition.startListening({ continuous: false });
    }
    setIsListening((prev) => !prev);
  };

  const handleSendMessage = (inputPrompt: string) => {
    if (inputPrompt.trim() === "") return;

    const newMessage = { text: inputPrompt, sender: "user" };
    setMessages((prevMessages) => [...prevMessages, newMessage]);
    setPrompt("");
    resetTranscript();
    setIsProcessing(true);

    const controller = new AbortController(); // Create a new AbortController instance
    setAbortController(controller); // Store the controller

    fetch("http://localhost:8000/ask", {
      method: "POST",
      body: JSON.stringify({ question: inputPrompt }),
      headers: {
        "Content-Type": "application/json",
      },
      signal: controller.signal, // Pass the abort signal to fetch
    })
      .then((res) => {
        if (!res.ok) {
          throw new Error("Network response was not ok");
        }
        return res.json();
      })
      .then((data) => {
        // speak(data.answer);
        const aiMessage = { text: data.answer, sender: "ai" };
        setMessages((prev) => [...prev, aiMessage]);
        setIsProcessing(false);
      })
      .catch((error) => {
        if (error.name === "AbortError") {
          console.log("Fetch request was aborted");
        } else {
          console.error("Fetch error:", error);
        }
      })
      .finally(() => {
        setIsProcessing(false);
      });
  };

  const handleCancelProcessing = () => {
    if (abortController) {
      abortController.abort(); // Abort the fetch request
      setAbortController(null); // Clear the abort controller
    }
    setIsProcessing(false);
  };

  return (
    <main className="h-screen grid grid-cols-[12vw_1fr] font-mont max-md:grid-cols-1 w-screen">
      <aside className="flex flex-col py-6 px-4 border-r items-center justify-between max-md:hidden">
        <img src="/alunet.png" alt="Alunet Systems Logo" className="w-40 m-2" />
        {/* <img src="/arkay.jpeg" alt="Arkay Windows Logo" className="w-40 m-2" /> */}
        <div className="w-full bg-fill/[0.1] h-14 rounded-md border gap-4 flex items-center px-2">
          <div className="size-10 bg-fill rounded-full"></div>
          <div>
            <p className="font-semibold text-[2vw] sm:text-[0.4vw] md:text-[0.5vw] lg:text-[0.6vw] xl:text-[0.8vw] flex">
              Tim
            </p>
            <p className="text-[2vw] sm:text-[0.3vw] md:text-[0.4vw] lg:text-[0.5vw] xl:text-[0.6vw]">
              Customer
            </p>
          </div>
        </div>
      </aside>

      <section className="px-72 bg-slate-100 relative max-md:px-10">
        <div className=" relative py-10 flex flex-col items-center">
          {messages.length === 0 ? (
            <>
              <p className="font-bold text-3xl py-4 px-8 max-md:px-4 max-md:py-2 max-md:text-xl text-primary bg-white rounded-full border">
                Aluna AI
              </p>
              <motion.div
                className="text-3xl font-medium mt-8 max-md:mt-3 opacity-80 max-md:text-lg"
                initial="hidden"
                animate="visible"
                variants={{
                  hidden: { opacity: 0, y: 20 },
                  visible: {
                    opacity: 1,
                    y: 0,
                    transition: {
                      duration: 0.5,
                    },
                  },
                }}
              >
                Good Day, How may I help you?
              </motion.div>
              <img
                src="/msbc-logo.png"
                alt="Company Logo"
                className="mt-32 w-56 md:hidden"
              />
              <motion.div
                className="grid grid-cols-2 w-full gap-x-6 gap-y-10 pt-10 max-md:hidden"
                initial="hidden"
                animate="visible"
                variants={{
                  hidden: { opacity: 0 },
                  visible: {
                    opacity: 1,
                    transition: {
                      staggerChildren: 0.2,
                    },
                  },
                }}
              >
                {[
                  {
                    Icon: TbHelpHexagonFilled,
                    title: "Answer",
                    text: "What's the batch size of bulk order?",
                  },
                  {
                    Icon: GoAlertFill,
                    title: "Inquiry",
                    text: "What are the available products?",
                  },
                  {
                    Icon: GoCheckCircleFill,
                    title: "Support",
                    text: "Need assistance with selecting what is right for you?",
                  },
                  {
                    Icon: GoCodeSquare,
                    title: "Analysis",
                    text: "An expert review and comparison of the best products",
                  },
                  {
                    Icon: GoGitPullRequest,
                    title: "Escalate Issue",
                    text: "Connect to our talented team for further assistance",
                  },
                  {
                    Icon: GoFlame,
                    title: "Become a Vendor",
                    text: "Join our network of vendors and grow your business",
                  },
                ].map((card, index) => (
                  <motion.div
                    key={index}
                    variants={{
                      hidden: { opacity: 0, y: 20 },
                      visible: { opacity: 1, y: 0 },
                    }}
                    transition={{ duration: 0.5 }}
                  >
                    <AiCard
                      Icon={card.Icon}
                      title={card.title}
                      text={card.text}
                    />
                  </motion.div>
                ))}
              </motion.div>
            </>
          ) : (
            <div className="w-full flex flex-col gap-4 overflow-y-scroll mb-24">
              {messages.map((msg, index) => (
                <div key={index} className="flex items-center">
                  {msg.sender === "user" ? (
                    <div className="flex flex-col ">
                      <p className="font-medium bg-white px-2 py-2 border rounded-full">
                        <Typewriter
                          words={[msg.text]}
                          typeSpeed={2}
                          cursorStyle={"|"}
                          delaySpeed={3}
                        />
                      </p>
                      {/* <p className="font-medium bg-white px-2 py-2 border rounded-full">{msg.text}</p> */}
                    </div>
                  ) : (
                    <div className="flex flex-col rounded-full">
                      <p className="font-medium mt-2">
                        <Markdown>{msg.text}</Markdown>
                      </p>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="flex justify-center items-end pb-4 overflow-hidden">
          {" "}
          {/* Changed items-center to items-end */}
          <form
            onSubmit={(e) => {
              e.preventDefault();
              handleSendMessage(prompt);
            }}
            className="bg-white rounded-full border flex items-center justify-between px-4 w-[90%] md:w-[60%] lg:w-[50%] max-w-[800px] py-2 h-16 fixed bottom-6"
          >
            <input
              type="text"
              className="rounded-full h-12 w-full focus:outline-none pl-4" // Added pl-4 for left padding
              placeholder="Ask me anything"
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
            />

            <div className="flex items-center">
              {!isProcessing && (
                <FaMicrophoneAlt
                  className={`${
                    listening
                      ? "text-red-500 animate-pulse"
                      : "hover:text-slate-600 text-slate-500"
                  } text-2xl cursor-pointer transition-colors`}
                  onClick={handleMicClick}
                />
              )}
              {!isProcessing && (
                <>
                  {isListening ? (
                    <FaStopCircle
                      className="text-red-500 text-2xl ml-4 cursor-pointer hover:text-red-600 transition-colors"
                      onClick={handleMicClick}
                    />
                  ) : (
                    <GrSend
                      className="text-slate-500 text-2xl ml-4 hover:text-slate-600 cursor-pointer transition-colors"
                      onClick={() => handleSendMessage(prompt)}
                    />
                  )}
                </>
              )}

              {isProcessing && (
                <FaStop
                  className="text-slate-500 text-2xl ml-4 hover:text-slate-600 cursor-pointer transition-colors animate-pulse"
                  onClick={handleCancelProcessing}
                />
              )}
            </div>
          </form>
        </div>
      </section>
    </main>
  );
}

export default chatbot;
