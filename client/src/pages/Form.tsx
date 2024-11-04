import { useState, useContext, useEffect, forwardRef } from "react";
import { useNavigate } from "react-router-dom";
import { HOST } from "../../config";
import {
  Typography,
  TextField,
  Button,
  MenuItem,
  InputLabel,
  FormControl,
  Select,
  IconButton,
  InputAdornment,
  CircularProgress,
} from "@mui/material";
import AddIcon from "@mui/icons-material/Add";
import { ThemeProvider, ThemeContext } from "../context/ThemeContext.jsx";
import Header from "../components/Header.jsx";
import RemoveIcon from "@mui/icons-material/Remove";
import Ellipse1 from "../assets/images/Ellipse1.svg";
import Ellipse2 from "../assets/images/Ellipse2.svg";
import Ellipse3 from "../assets/images/Ellipse3.svg";
import Ellipse4 from "../assets/images/Ellipse4.svg";
import toast from "react-hot-toast";

function Form() {
  const { theme } = useContext(ThemeContext);
  const [formData, setFormData] = useState({
    company_url: "",
    company_name: "",
    logo: null,
    additionalWebsites: [""],
    persona: "",
    attachments: [],
    customer_name: "",
    timeout_seconds: "30",
  });
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const handleRemoveWebsiteField = (index: number) => {
    const newWebsites = formData.additionalWebsites.filter(
      (_, i) => i !== index
    );
    setFormData({ ...formData, additionalWebsites: newWebsites });
  };

  const handleFileChange = (e: any) => {
    const file = e.target.files[0];
    if (file && ["image/jpeg", "image/jpg", "image/png"].includes(file.type)) {
      setFormData({ ...formData, logo: file });
    } else {
      toast.error(
        "Invalid Image Format. Supported File format are : jpeg, jpg and png"
      );
    }
  };

  const handleAttachmentsChange = (e: any) => {
    const files = Array.from(e.target.files);
    const validFiles = files.filter((file) =>
      [
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        //@ts-ignore
      ].includes(file.type)
    );

    if (validFiles.length === files.length) {
      //@ts-ignore
      setFormData({ ...formData, attachments: validFiles });
    } else {
      toast.error(
        "Invalid attachment format, allowed formats are docx, pdf and ppt"
      );
    }
  };

  const handleAddWebsiteField = () => {
    setFormData({
      ...formData,
      additionalWebsites: [...formData.additionalWebsites, ""],
    });
  };

  //@ts-ignore
  const handleWebsiteChange = (index, value) => {
    const newWebsites = [...formData.additionalWebsites];
    newWebsites[index] = value;
    setFormData({ ...formData, additionalWebsites: newWebsites });
  };

  //@ts-ignore
  const checkScrapingStatus = async (companyName) => {
    try {
      const response = await fetch(`${HOST}/scraping_status/${companyName}`);
      const result = await response.json();
      if (response.ok && result.status != "In Progress") {
        setLoading(false);
        toast(
          (t) => (
            <span>
              Scraping session completed. Proceed to Chatbot?
              <br />
              <button
                onClick={() => {
                  navigate(
                    `/chatbot?company=${formData.company_name
                      .toLowerCase()
                      .replace(" ", "_")}`
                  );
                  toast.dismiss(t.id);
                }}
                className="bg-black p-2 font-bold text-white mt-2"
              >
                Yes
              </button>
              <button
                onClick={() => toast.dismiss(t.id)}
                className="bg-red-600 p-2 font-bold text-white mt-2 ml-2"
              >
                No
              </button>
            </span>
          ),
          {
            duration: 60000,
          }
        );
      } else {
        //* Handle Progress Bar here
        setTimeout(() => checkScrapingStatus(companyName), 5000);
      }
    } catch (error) {
      console.error("Error checking scraping status:", error);
      setLoading(false);
      toast.error("Something went wrong while checking scraping status");
    }
  };

  const handleSubmit = async (e: any) => {
    e.preventDefault();

    const data = new FormData();
    data.append("company_url", formData.company_url);
    data.append("company_name", formData.company_name);
    if (formData.logo) data.append("logo", formData.logo);
    data.append("additional_websites", formData.additionalWebsites.join(", "));
    data.append("timeout_seconds", formData.timeout_seconds);
    data.append("persona", formData.persona);
    if (formData.customer_name)
      data.append("customer_name", formData.customer_name);
    formData.attachments.forEach((file) => data.append("attachments", file));

    setLoading(true);

    try {
      const response = await fetch(`${HOST}/scrap`, {
        method: "POST",
        body: data,
      });

      if (response.ok) {
        toast.success("Form saved, starting scraping session");

        checkScrapingStatus(
          formData.company_name.toLowerCase().replace(" ", "_")
        );
      } else {
        const result = await response.json();
        toast.error(result.message);
        setLoading(false);
      }
    } catch (error) {
      toast.error(
        "The server didn't respond, Are you sure the server is running?"
      );
      setLoading(false);
    }
  };

  return (
    <div
      style={{
        height: "100vh",
        width: "100vw",
        display: "flex",
        alignItems: "center",
        flexDirection: "column",
        position: "relative",
      }}
    >
      <img
        src={Ellipse1}
        alt="Circle-or"
        className="circle1"
        style={{
          position: "absolute",
          right: "0vw",
          bottom: "10vh",
          width: "50vw",
          zIndex: -1,
        }}
      />
      <img
        src={Ellipse2}
        alt="Circle-blue"
        className="circle2"
        style={{
          position: "absolute",
          right: "10vw",
          bottom: "30vh",
          width: "6vw",
          zIndex: -1,
        }}
      />
      <img
        src={Ellipse3}
        alt="Circle-blue"
        className="circle3"
        style={{
          position: "absolute",
          left: "0vw",
          bottom: "20vh",
          width: "9vw",
          zIndex: -1,
        }}
      />
      <img
        src={Ellipse4}
        alt="Circle-or"
        className="circle4"
        style={{
          position: "absolute",
          left: "10vw",
          top: "14vh",
          width: "6vw",

          zIndex: -1,
        }}
      />

      <div
        style={{
          marginTop: "50px",
          backgroundColor: theme.backgroundColor,
          borderRadius: "8px",
          padding: "2vh 3vw",
          boxShadow: "0 2px 10px rgba(0, 0, 0, 0.1)",
          border: "solid 1px #d7d7d7",
          fontFamily: "Montserrat",
          minHeight: "70vh",
          maxHeight: "80vh",
          display: "flex",
          flexDirection: "column",
          overflowY: "auto",
        }}
      >
        <Typography
          variant="h5"
          align="center"
          gutterBottom
          sx={{ color: "#243a57", fontFamily: "Montserrat" }}
        >
          Company Information Form
        </Typography>

        <form onSubmit={handleSubmit}>
          <TextField
            fullWidth
            label="Website*"
            variant="outlined"
            placeholder="www.msbcgroup.com"
            value={formData.company_url}
            onChange={(e) =>
              setFormData({ ...formData, company_url: e.target.value })
            }
            margin="normal"
            sx={{
              "& .MuiOutlinedInput-root": {
                "& fieldset": {
                  borderColor: "#d7d7d7",
                  borderRadius: "8px",
                },
                "&:hover fieldset": {
                  borderColor: "#ff9800",
                },
                "&.Mui-focused fieldset": {
                  borderColor: "#243a57",
                },
              },
              "& .MuiOutlinedInput-input": {
                color: "#243a57",
                backgroundColor: "transparent",
              },
              "& .MuiOutlinedInput-root.Mui-focused": {
                backgroundColor: "transparent",
              },
              "&:hover": {
                backgroundColor: "transparent",
              },
            }}
          />

          <TextField
            fullWidth
            label="Company Name*"
            variant="outlined"
            placeholder="MSBC Group"
            value={formData.company_name}
            onChange={(e) =>
              setFormData({ ...formData, company_name: e.target.value })
            }
            sx={{
              "& .MuiOutlinedInput-root": {
                "& fieldset": {
                  borderColor: "#d7d7d7",
                  borderRadius: "8px",
                },
                "&:hover fieldset": {
                  borderColor: "#ff9800",
                },
                "&.Mui-focused fieldset": {
                  borderColor: "#243a57",
                },
              },
              "& .MuiOutlinedInput-input": {
                color: "#243a57",
                backgroundColor: "transparent",
              },
              "& .MuiOutlinedInput-root.Mui-focused": {
                backgroundColor: "transparent",
              },
              "&:hover": {
                backgroundColor: "transparent",
              },
            }}
          />

          <TextField
            fullWidth
            type="file"
            label="Company Logo"
            variant="outlined"
            onChange={handleAttachmentsChange}
            margin="normal"
            InputLabelProps={{
              shrink: true,
              style: {
                fontFamily: "Montserrat",
                color: "#243a57",
                fontWeight: "550",
              },
            }}
            inputProps={{ multiple: true }}
            sx={{
              "& .MuiOutlinedInput-root": {
                "& fieldset": {
                  borderColor: "#d7d7d7",
                  borderRadius: "8px",
                },
                "&:hover fieldset": {
                  borderColor: "#ff9800",
                },
                "&.Mui-focused fieldset": {
                  borderColor: "#243a57",
                },
              },
              "& .MuiOutlinedInput-input": {
                color: "#243a57",
                backgroundColor: "transparent",
              },
              "& .MuiOutlinedInput-root.Mui-focused": {
                backgroundColor: "transparent",
              },
              "&:hover": {
                backgroundColor: "transparent",
              },
            }}
          />

          {formData.additionalWebsites.map((company_url, index) => (
            <div
              key={index}
              style={{
                display: "flex",
                alignItems: "center",
                marginBottom: "10px",
                width: "100%",
              }}
            >
              <TextField
                fullWidth
                label={`Additional Website #${index + 1}`}
                variant="outlined"
                placeholder="www.additional.com"
                value={company_url}
                onChange={(e) => handleWebsiteChange(index, e.target.value)}
                margin="normal"
                InputProps={{
                  endAdornment: (
                    <InputAdornment position="end">
                      {index > 0 && (
                        <IconButton
                          onClick={() => handleRemoveWebsiteField(index)}
                          color="error"
                          size="small"
                        >
                          <RemoveIcon />
                        </IconButton>
                      )}
                      <IconButton onClick={handleAddWebsiteField} size="small">
                        <AddIcon />
                      </IconButton>
                    </InputAdornment>
                  ),
                }}
                sx={{
                  "& .MuiOutlinedInput-root": {
                    "& fieldset": {
                      borderColor: "#d7d7d7",
                      borderRadius: "8px",
                    },
                    "&:hover fieldset": {
                      borderColor: "#ff9800",
                    },
                    "&.Mui-focused fieldset": {
                      borderColor: "#243a57",
                    },
                  },
                  "& .MuiOutlinedInput-input": {
                    color: "#243a57",
                    backgroundColor: "transparent",
                  },
                  "& .MuiOutlinedInput-root.Mui-focused": {
                    backgroundColor: "transparent",
                  },
                  "&:hover": {
                    backgroundColor: "transparent",
                  },
                }}
              />
            </div>
            
          ))}

          <FormControl fullWidth margin="normal">
            <InputLabel
              style={{
                fontFamily: "Montserrat",
                color: "#243a57",
                fontWeight: "550",
              }}
              shrink
            >
              Select Persona*
            </InputLabel>
            <Select
              value={formData.persona}
              onChange={(e) =>
                setFormData({ ...formData, persona: e.target.value })
              }
              label="Select Persona"
              displayEmpty
              inputProps={{
                sx: {
                  borderRadius: "8px",
                },
              }}
            >
              <MenuItem value="">
                <em>Select Persona</em>
              </MenuItem>
              <MenuItem value="Happy Helper">Happy Helper</MenuItem>
              <MenuItem value="Strict Instructor">Strict Instructor</MenuItem>
            </Select>
          </FormControl>

          <TextField
            fullWidth
            label="Customer Name"
            variant="outlined"
            placeholder="Mr. Parker"
            value={formData.customer_name}
            onChange={(e) =>
              setFormData({ ...formData, customer_name: e.target.value })
            }
            margin="normal"
            sx={{
              "& .MuiOutlinedInput-root": {
                "& fieldset": {
                  borderColor: "#d7d7d7",
                  borderRadius: "8px",
                },
                "&:hover fieldset": {
                  borderColor: "#ff9800",
                },
                "&.Mui-focused fieldset": {
                  borderColor: "#243a57",
                },
              },
              "& .MuiOutlinedInput-input": {
                color: "#243a57", // Input text color
                backgroundColor: "transparent",
              },
              "& .MuiOutlinedInput-root.Mui-focused": {
                backgroundColor: "transparent",
              },
              "&:hover": {
                backgroundColor: "transparent",
              },
            }}
          />

          <TextField
            fullWidth
            type="file"
            label="Attachments"
            variant="outlined"
            // placeholder="file.pdf"
            onChange={handleAttachmentsChange}
            margin="normal"
            InputLabelProps={{
              shrink: true,
              style: {
                fontFamily: "Montserrat",
                color: "#243a57",
                fontWeight: "550",
              },
            }}
            inputProps={{ multiple: true }}
            sx={{
              "& .MuiOutlinedInput-root": {
                "& fieldset": {
                  borderColor: "#d7d7d7",
                  borderRadius: "8px",
                },
                "&:hover fieldset": {
                  borderColor: "#ff9800",
                },
                "&.Mui-focused fieldset": {
                  borderColor: "#243a57",
                },
              },
              "& .MuiOutlinedInput-input": {
                color: "#243a57",
                backgroundColor: "transparent",
              },
              "& .MuiOutlinedInput-root.Mui-focused": {
                backgroundColor: "transparent",
              },
              "&:hover": {
                backgroundColor: "transparent",
              },
            }}
          />
          <TextField
            fullWidth
            type="text"
            label="Timeout in Seconds"
            variant="outlined"
            onChange={(e) => {
              setFormData({
                ...formData,
                timeout_seconds: e.target.value,
              });
            }}
            margin="normal"
            sx={{
              "& .MuiOutlinedInput-root": {
                "& fieldset": {
                  borderColor: "#d7d7d7",
                  borderRadius: "8px",
                },
                "&:hover fieldset": {
                  borderColor: "#ff9800",
                },
                "&.Mui-focused fieldset": {
                  borderColor: "#243a57",
                },
              },
              "& .MuiOutlinedInput-input": {
                color: "#243a57",
                backgroundColor: "transparent",
              },
              "& .MuiOutlinedInput-root.Mui-focused": {
                backgroundColor: "transparent",
              },
              "&:hover": {
                backgroundColor: "transparent",
              },
            }}
          />

          <Button
            variant="contained"
            type="submit"
            fullWidth
            sx={{
              fontFamily: "Montserrat",
              backgroundColor: "#243a57",
              borderRadius: "8px",
              marginTop: "30px",
              marginBottom: "10px",
            }}
            disabled={loading}
          >
            {loading ? (
              <CircularProgress size={24} color="inherit" />
            ) : (
              "Submit"
            )}
          </Button>
        </form>
      </div>
    </div>
  );
}

const WrappedApp = () => (
  <ThemeProvider>
    <Header />
    <Form />
  </ThemeProvider>
);

export default WrappedApp;
