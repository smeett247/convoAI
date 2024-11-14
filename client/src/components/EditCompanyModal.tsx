import React, { useState, useEffect } from "react";
import toast from "react-hot-toast";
import { HOST } from "../../config";
import { FormControl, InputLabel, Select, MenuItem, TextField, Button, IconButton } from "@mui/material";
import { AddCircleOutline, RemoveCircleOutline } from "@mui/icons-material";

interface EditCompanyModalProps {
  company: any; // You can replace `any` with a specific company type if you have one
  onClose: () => void;
}

const EditCompanyModal: React.FC<EditCompanyModalProps> = ({ company, onClose }) => {
  const [companyName, setCompanyName] = useState<string>(company?.company_name || "");
  const [companyUrl, setCompanyUrl] = useState<string>(company?.company_url || "");
  const [persona, setPersona] = useState<string>(company?.persona || "");
  const [instructions, setInstructions] = useState<string>(company?.instructions || "");
  const [timeoutMinutes, setTimeoutMinutes] = useState<number>(Math.floor(company?.timeout_seconds / 60) || 0);
  const [timeoutSeconds, setTimeoutSeconds] = useState<number>(company?.timeout_seconds % 60 || 0);
  const [additionalWebsites, setAdditionalWebsites] = useState<string[]>(company?.additionalWebsites || [""]);
  const [attachments, setAttachments] = useState<(File | string)[]>(company?.attachments || []);
  const [logo, setLogo] = useState<File | string | null>(company?.logo || null);
  const [viewAttachment, setViewAttachment] = useState<string | null>(null);

  useEffect(() => {
    if (company?.attachments) setAttachments(company.attachments);
    if (company?.logo) setLogo(company.logo);
  }, [company]);

  const handleSave = async () => {
    try {
      const totalTimeoutSeconds = timeoutMinutes * 60 + timeoutSeconds;
      const formData = {
        company_name: companyName,
        company_url: companyUrl,
        persona,
        instructions,
        timeout_seconds: totalTimeoutSeconds,
        additionalWebsites,
        attachments,
        logo,
      };
  
      const response = await fetch(`${HOST}/companies/${company?.company_name}`, {
        method: "PUT",  // Ensure that PUT is supported in the backend
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(formData),
      });
  
      if (!response.ok) {
        throw new Error("Failed to update company");
      }
  
      await toast.promise(response, {
        loading: "Saving...",
        success: "Company updated successfully!",
        error: "Failed to update company",
      });
  
      onClose();
    } catch (error) {
      console.error(error);
      toast.error("Failed to update company");
    }
  };

  const handleLogoChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files ? e.target.files[0] : null;
    if (file && file instanceof File) {
      setLogo(file);
    } else {
      setLogo(null);
      console.error("Invalid file selected for logo");
    }
  };

  const handleAttachmentChange = (e: React.ChangeEvent<HTMLInputElement>, index: number) => {
    const file = e.target.files ? e.target.files[0] : null;
    if (file) {
      const newAttachments = [...attachments];
      newAttachments[index] = file;
      setAttachments(newAttachments);
    }
  };

  const handleRemoveAttachment = (index: number) => {
    const newAttachments = attachments.filter((_, i) => i !== index);
    setAttachments(newAttachments);
  };

  const handleRemoveLogo = () => {
    setLogo(null);
  };

  const handleViewAttachment = (attachment: string) => {
    setViewAttachment(attachment);
  };

  const handleAddWebsite = () => {
    setAdditionalWebsites([...additionalWebsites, ""]);
  };

  const handleRemoveWebsite = (index: number) => {
    const newWebsites = additionalWebsites.filter((_, i) => i !== index);
    setAdditionalWebsites(newWebsites);
  };

  return (
    <div className="fixed inset-0 flex items-center justify-center bg-gray-800 bg-opacity-50 z-50">
      <div className="bg-white rounded-lg p-6 w-[90vw] max-w-lg shadow-lg overflow-auto" style={{ maxHeight: '80vh' }}>
        <h2 className="text-lg font-bold mb-4 ">Edit Company</h2>

        <TextField
          fullWidth
          label="Company Name"
          value={companyName}
          onChange={(e) => setCompanyName(e.target.value)}
          margin="normal"
        />

        <TextField
          fullWidth
          label="Company URL"
          value={companyUrl}
          disabled
          margin="normal"
        />

        <FormControl fullWidth margin="normal">
          <InputLabel shrink>Select Persona*</InputLabel>
          <Select
            value={persona}
            onChange={(e) => setPersona(e.target.value)}
            displayEmpty
            label="Select Persona"
          >
            <MenuItem value="">
              <em>Select Persona</em>
            </MenuItem>
            <MenuItem value="Happy Helper">Happy Helper</MenuItem>
            <MenuItem value="Strict Instructor">Strict Instructor</MenuItem>
            <MenuItem value="Custom Persona">Custom Persona</MenuItem>
          </Select>
        </FormControl>

        {persona === "Custom Persona" && (
          <>
            <TextField
              fullWidth
              label="Enter Persona Name"
              variant="outlined"
              margin="normal"
            />
            <TextField
              fullWidth
              label="Enter Custom Instructions*"
              variant="outlined"
              value={instructions || ""}
              onChange={(e) => setInstructions(e.target.value)}
              margin="normal"
            />
          </>
        )}

        {/* <div className="flex gap-2 mb-4">
          <TextField
            label="Minutes"
            type="number"
            value={timeoutMinutes}
            onChange={(e) => setTimeoutMinutes(Math.max(0, parseInt(e.target.value) || 0))}
            margin="normal"
            fullWidth
          />
          <TextField
            label="Seconds"
            type="number"
            value={timeoutSeconds}
            onChange={(e) => setTimeoutSeconds(Math.max(0, Math.min(59, parseInt(e.target.value) || 0)))}
            margin="normal"
            fullWidth
          />
        </div> */}

        <div className="mb-4">
          {additionalWebsites.map((website, index) => (
            <div key={index} className="flex gap-2 mb-2">
              <TextField
                fullWidth
                label={`Website ${index + 1}`}
                value={website}
                onChange={(e) => {
                  const newWebsites = [...additionalWebsites];
                  newWebsites[index] = e.target.value;
                  setAdditionalWebsites(newWebsites);
                }}
                margin="normal"
              />
              <IconButton
                color="error"
                size="small"
                onClick={() => handleRemoveWebsite(index)}
              >
                <RemoveCircleOutline />
              </IconButton>
            </div>
          ))}
          <Button
            variant="contained"
            onClick={handleAddWebsite}
            className="mt-2"
            startIcon={<AddCircleOutline />}
          >
            Add Website
          </Button>
        </div>

        <div className="mb-4">
          <h3 className="text-lg">Attachments</h3>
          {attachments.map((attachment, index) => (
            <div key={index} className="flex flex-col gap-2 mb-2">
              <div className="flex gap-2">
                {attachment && typeof attachment === "string" ? (
                  <a href={attachment} target="_blank" rel="noopener noreferrer">
                    {attachment}
                  </a>
                ) : (
                  <span>{(attachment as File)?.name || "No file selected"}</span>
                )}
                <Button
                  variant="outlined"
                  color="error"
                  size="small"
                  onClick={() => handleRemoveAttachment(index)}
                >
                  Delete
                </Button>
                <Button
                  variant="outlined"
                  color="primary"
                  size="small"
                  onClick={() => handleViewAttachment(attachment as string)}
                >
                  View
                </Button>
              </div>

              {viewAttachment === (attachment as string) && (
                <div className="mt-2">
                  {viewAttachment.endsWith(".pdf") ? (
                    <iframe
                      src={viewAttachment}
                      width="100%"
                      height="500px"
                      title="Attachment Preview"
                    ></iframe>
                  ) : (
                    <img
                      src={viewAttachment}
                      alt="Attachment"
                      className="max-w-full max-h-[500px] object-contain"
                    />
                  )}
                </div>
              )}

              <input
                type="file"
                onChange={(e) => handleAttachmentChange(e, index)}
                accept="image/*, application/pdf"
                className="mt-2"
              />
            </div>
          ))}
          <Button
            variant="contained"
            onClick={() => setAttachments([...attachments, ""])}
            className="mt-2"
          >
            Add Attachment
          </Button>
        </div>

        <div className="flex justify-between">
          <Button onClick={onClose} variant="outlined">
            Cancel
          </Button>
          <Button onClick={handleSave} variant="contained" color="primary">
            Save Changes
          </Button>
        </div>
      </div>
    </div>
  );
};

export default EditCompanyModal;