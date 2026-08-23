import "./AlertBanner.css";

export default function AlertBanner({ tone = "error", children }) {
  if (!children) return null;
  return (
    <div className={`alert-banner alert-banner--${tone}`} role="alert">
      {children}
    </div>
  );
}
