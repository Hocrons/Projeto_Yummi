import Logo from "./Logo";
import "./AuthLayout.css";

export default function AuthLayout({ eyebrow = "Yummi", title, subtitle, children }) {
  return (
    <div className="auth-page">
      <p className="auth-page__eyebrow">{eyebrow}</p>
      <div className="auth-card">
        <div className="auth-card__brand">
          <Logo />
        </div>
        <h1 className="auth-card__title">{title}</h1>
        {subtitle ? <p className="auth-card__subtitle">{subtitle}</p> : null}
        {children}
      </div>
    </div>
  );
}
