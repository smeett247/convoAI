import Logo from "../assets/images/msbc-logo.png";
import "../assets/css/Header.css";

/**
 * A header component with a company logo and title.
 */
export default function Header(): JSX.Element {
  return (
    <div className="header">
      <div className="toolbar">
        <div className="logo-container">
          <img src={Logo} alt="Company Logo" className="logo" />
        </div>
        <div className="title">Conversational AI</div>
      </div>
    </div>
  );
}
