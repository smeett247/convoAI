
import React from "react";
import Logo from "./assets/msbc-logo (2).png";
import "./Header.css";  // Importing CSS for styling

const Header = () => {
  return (
    <div className="header">
      <div className="toolbar">
        {/* Logo */}
        <div className="logo-container">
          <img src={Logo} alt="Company Logo" className="logo" />
        </div>

        {/* Title */}
        <div className="title">
          Conversational AI
        </div>
      </div>
    </div>
  );
};

export default Header;
