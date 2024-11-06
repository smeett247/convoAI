import { createContext, useState } from "react";

export type Theme = {
  backgroundColor: string;
  textColor: string;
  primaryColor: string;
  secondaryColor: string;
  errorColor: string;
};

const ThemeContext = createContext<{
  theme: Theme;
  setTheme: (theme: Theme) => void;
} | null>(null);

/**
 * ThemeProvider component.
 *
 * @param {{ children: JSX.Element | JSX.Element[] }} props The props object.
 * @prop {JSX.Element | JSX.Element[]} children The children elements to wrap.
 *
 * The ThemeProvider component wraps the given children elements with a ThemeContext.Provider.
 * It initializes the theme state with a default theme, and provides a setTheme function to update the theme.
 *
 * The default theme is:
 * {
 *   backgroundColor: "#f9f9f9",
 *   textColor: "#000",
 *   primaryColor: "#4CAF50",
 *   secondaryColor: "#2A2A2A",
 *   errorColor: "#f44336",
 * }
 *
 * The ThemeProvider component must be used as the most outer component in the application.
 */
const ThemeProvider = ({
  children,
}: {
  children: JSX.Element | JSX.Element[];
}) => {
  const [theme, setTheme] = useState<Theme>({
    backgroundColor: "#f9f9f9",
    textColor: "#000",
    primaryColor: "#4CAF50",
    secondaryColor: "#2A2A2A",
    errorColor: "#f44336",
  });

  return (
    <ThemeContext.Provider value={{ theme, setTheme }}>
      {children}
    </ThemeContext.Provider>
  );
};

export { ThemeContext, ThemeProvider };
