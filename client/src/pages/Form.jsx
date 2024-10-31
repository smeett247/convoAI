import { useState, useContext, useEffect, forwardRef } from "react";
import { useNavigate } from "react-router-dom";
import { HOST } from "../../config";
import {
  Container,
  Typography,
  TextField,
  Button,
  MenuItem,
  InputLabel,
  FormControl,
  Select,
  Snackbar,
  IconButton,
  InputAdornment,
  CircularProgress,
  Dialog,
  DialogActions,
  DialogContent,
  DialogContentText,
  DialogTitle,
} from "@mui/material";
import AddIcon from "@mui/icons-material/Add";
import MuiAlert from "@mui/material/Alert";
import { ThemeProvider, ThemeContext } from "../context/ThemeContext.jsx";
import Header from "../components/Header.jsx";
import RemoveIcon from "@mui/icons-material/Remove";
import Ellipse1 from "../assets/images/Ellipse1.svg";
import Ellipse2 from "../assets/images/Ellipse2.svg";
import Ellipse3 from "../assets/images/Ellipse3.svg";
import Ellipse4 from "../assets/images/Ellipse4.svg";

const Alert = forwardRef((props, ref) => (
  <MuiAlert elevation={6} ref={ref} variant="filled" {...props} />
));

function Form() {
  const { theme } = useContext(ThemeContext);
  const navigate = useNavigate();

  const [formData, setFormData] = useState({
    company_url: "",
    company_name: "",
    logo: null,
    additionalWebsites: [""],
    persona: "",
    attachments: [],
    customer_name: "",
  });

  const [errors, setErrors] = useState({});
  const [openSnackbar, setOpenSnackbar] = useState(false);
  const [snackbarMessage, setSnackbarMessage] = useState("");
  const [loading, setLoading] = useState(false);
  const [showDialog, setShowDialog] = useState(false);

  const handleRemoveWebsiteField = (index) => {
    const newWebsites = formData.additionalWebsites.filter(
      (_, i) => i !== index
    );
    setFormData({ ...formData, additionalWebsites: newWebsites });
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData((prevData) => ({ ...prevData, [name]: value }));
  };

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file && ["image/jpeg", "image/jpg", "image/png"].includes(file.type)) {
      setFormData({ ...formData, logo: file });
    } else {
      setSnackbarMessage("Please upload a valid image file (JPG, JPEG, PNG)");
      setOpenSnackbar(true);
    }
  };

  const handleAttachmentsChange = (e) => {
    const files = Array.from(e.target.files);
    const validFiles = files.filter((file) =>
      [
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
      ].includes(file.type)
    );

    if (validFiles.length === files.length) {
      setFormData({ ...formData, attachments: validFiles });
    } else {
      setSnackbarMessage(
        "Please upload valid attachments (PDF, Word, PowerPoint, Excel)"
      );
      setOpenSnackbar(true);
    }
  };

  const handleCloseSnackbar = () => {
    setOpenSnackbar(false);
  };

  const handleAddWebsiteField = () => {
    setFormData({
      ...formData,
      additionalWebsites: [...formData.additionalWebsites, ""],
    });
  };

  const handleWebsiteChange = (index, value) => {
    const newWebsites = [...formData.additionalWebsites];
    newWebsites[index] = value;
    setFormData({ ...formData, additionalWebsites: newWebsites });
  };

  // Polling function to check scraping status
  const checkScrapingStatus = async (companyName) => {
    try {
      const response = await fetch(`${HOST}/companies/${companyName}`);
      const result = await response.json();

      if (response.ok && result.scraping_complete) {
        setLoading(false);
        setShowDialog(true);
      } else {
        setTimeout(() => checkScrapingStatus(companyName), 3000);
      }
    } catch (error) {
      console.error("Error checking scraping status:", error);
      setLoading(false);
      setSnackbarMessage("Failed to check scraping status.");
      setOpenSnackbar(true);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    let validationErrors = {};
    if (!formData.company_name) {
      validationErrors.company_name = "Company name is required";
    }
    if (!formData.persona) {
      validationErrors.persona = "Persona selection is required";
    }

    setErrors(validationErrors);

    if (Object.keys(validationErrors).length === 0) {
      const data = new FormData();
      data.append("company_url", formData.company_url);
      data.append("company_name", formData.company_name);
      if (formData.logo) data.append("logo", formData.logo);
      formData.additionalWebsites.forEach((url) => {
        if (url) data.append("additional_websites", url);
      });
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
          setSnackbarMessage(
            "Form submitted successfully! Starting scraping session!"
          );
          const result = await response.json();
          console.log("Response from server:", result);
          setLoading(false);
        } else {
          const result = await response.json();
          setSnackbarMessage(`Error: ${result.message}`);
          setLoading(false);
        }
      } catch (error) {
        console.log(error);
        setSnackbarMessage("Error: Failed to submit form. Please try again.");
        setLoading(false);
      } finally {
        setOpenSnackbar(true);
      }
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
          marginTop: "5vh", // Adjust for spacing
          backgroundColor: theme.backgroundColor,
          borderRadius: "8px",
          padding: "2vh 3vw", // Responsive padding
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
            error={!!errors.company_url}
            helperText={errors.company_url}
            margin="normal"
            InputLabelProps={{
              shrink: true,
              style: {
                color: errors.company_url ? "red" : "#243a57",
                fontWeight: "550",
                fontFamily: "Montserrat",
              },
            }}
            sx={{
              "& .MuiOutlinedInput-root": {
                "& fieldset": {
                  borderColor: errors.company_url ? "red" : "#d7d7d7",
                  borderRadius: "8px",
                },
                "&:hover fieldset": {
                  borderColor: errors.company_url ? "red" : "#ff9800",
                },
                "&.Mui-focused fieldset": {
                  borderColor: errors.company_url ? "red" : "#243a57",
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
            error={!!errors.company_name}
            helperText={errors.company_name}
            margin="normal"
            InputLabelProps={{
              shrink: true,
              style: {
                color: errors.company_name ? "red" : "#243a57",
                fontWeight: "550",
                fontFamily: "Montserrat",
              },
            }}
            sx={{
              "& .MuiOutlinedInput-root": {
                "& fieldset": {
                  borderColor: errors.company_url ? "red" : "#d7d7d7",
                  borderRadius: "8px",
                },
                "&:hover fieldset": {
                  borderColor: errors.company_url ? "red" : "#ff9800",
                },
                "&.Mui-focused fieldset": {
                  borderColor: errors.company_url ? "red" : "#243a57",
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
            label="Company Logo"
            variant="outlined"
            onChange={handleFileChange}
            margin="normal"
            InputLabelProps={{
              shrink: true,
              style: {
                fontFamily: "Montserrat",
                color: "#243a57",
                fontWeight: "550",
              },
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
                error={!!errors[`additionalWebsites${index}`]}
                helperText={errors[`additionalWebsites${index}`]}
                margin="normal"
                InputLabelProps={{
                  shrink: true,
                  style: {
                    fontFamily: "Montserrat",
                    color: "#243a57",
                    fontWeight: "550",
                  },
                }}
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
                      <IconButton
                        onClick={handleAddWebsiteField}
                        color="#243a57"
                        size="small"
                      >
                        <AddIcon />
                      </IconButton>
                    </InputAdornment>
                  ),
                }}
                sx={{
                  "& .MuiOutlinedInput-root": {
                    "& fieldset": {
                      borderColor: errors.company_url ? "red" : "#d7d7d7",
                      borderRadius: "8px",
                    },
                    "&:hover fieldset": {
                      borderColor: errors.company_url ? "red" : "#ff9800",
                    },
                    "&.Mui-focused fieldset": {
                      borderColor: errors.company_url ? "red" : "#243a57",
                    },
                  },
                  "& .MuiOutlinedInput-input": {
                    color: "#243a57",
                    backgroundColor: "transparent",
                  },
                  "& .MuiOutlinedInput-root.Mui-focused": {
                    backgroundColor: "transparent",
                  },
                }}
              />
            </div>
          ))}

          <FormControl fullWidth margin="normal" error={!!errors.persona}>
            <InputLabel
              style={{
                fontFamily: "Montserrat",
                color: errors.persona ? "red" : "#243a57",
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
              sx={{
                "& .MuiOutlinedInput-root": {
                  borderRadius: "8px",
                  "& fieldset": {
                    borderColor: errors.persona ? "red" : "#d7d7d7",
                    borderRadius: "8px",
                  },
                  "&:hover fieldset": {
                    borderColor: errors.persona ? "red" : "#ff9800",
                  },
                  "&.Mui-focused fieldset": {
                    borderColor: errors.persona ? "red" : "#243a57",
                  },
                },
                "& .MuiSelect-select": {
                  padding: "12px 14px",
                  fontFamily: "Montserrat",
                  color: "#243a57",
                },
              }}
            >
              <MenuItem value="">
                <em>Select Persona</em>
              </MenuItem>
              <MenuItem value="Happy Helper">Happy Helper</MenuItem>
              <MenuItem value="Strict Instructor">Strict Instructor</MenuItem>
            </Select>
            {errors.persona && (
              <span style={{ color: "red", fontFamily: "Montserrat" }}>
                {errors.persona}
              </span>
            )}
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
            InputLabelProps={{
              shrink: true,
              style: {
                fontFamily: "Montserrat",
                color: "#243a57",
                fontWeight: "550",
              },
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

        <Dialog open={showDialog} onClose={() => setShowDialog(false)}>
          <DialogTitle>Scraping Complete</DialogTitle>
          <DialogContent>
            <DialogContentText>
              Scraping is complete. Do you want to continue with the chatbot?
            </DialogContentText>
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setShowDialog(false)} color="primary">
              No
            </Button>
            <Button
              onClick={() => navigate("/chatbot")}
              color="primary"
              autoFocus
            >
              Yes
            </Button>
          </DialogActions>
        </Dialog>

        <Snackbar
          open={openSnackbar}
          autoHideDuration={6000}
          onClose={() => setOpenSnackbar(false)}
        >
          <Alert
            onClose={() => setOpenSnackbar(false)}
            severity={snackbarMessage.includes("Error") ? "error" : "success"}
          >
            {snackbarMessage}
          </Alert>
        </Snackbar>
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
