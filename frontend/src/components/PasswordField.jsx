import { useId, useState } from "react";
import "./FormField.css";

export default function PasswordField({ label, error, hint, ...inputProps }) {
  const id = useId();
  const [visivel, setVisivel] = useState(false);

  return (
    <div className="field">
      <label className="field__label" htmlFor={id}>
        {label}
      </label>
      <div className={`field__control ${error ? "field__control--error" : ""}`}>
        <input
          id={id}
          type={visivel ? "text" : "password"}
          className="field__input"
          {...inputProps}
        />
        <button
          type="button"
          className="field__toggle"
          onClick={() => setVisivel((v) => !v)}
          aria-label={visivel ? "Ocultar senha" : "Mostrar senha"}
          aria-pressed={visivel}
        >
          {visivel ? <IconEyeOff /> : <IconEye />}
        </button>
      </div>
      {error ? (
        <p className="field__message field__message--error" role="alert">
          {error}
        </p>
      ) : hint ? (
        <p className="field__message">{hint}</p>
      ) : null}
    </div>
  );
}

function IconEye() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path
        d="M1.5 12s4-7.5 10.5-7.5S22.5 12 22.5 12s-4 7.5-10.5 7.5S1.5 12 1.5 12Z"
        stroke="currentColor"
        strokeWidth="1.6"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <circle cx="12" cy="12" r="3" stroke="currentColor" strokeWidth="1.6" />
    </svg>
  );
}

function IconEyeOff() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path
        d="M3 3l18 18M10.6 10.7a3 3 0 0 0 4.24 4.24M6.6 6.7C3.9 8.4 1.5 12 1.5 12s4 7.5 10.5 7.5c2 0 3.7-.5 5.1-1.3M9.9 4.7A11 11 0 0 1 12 4.5c6.5 0 10.5 7.5 10.5 7.5a17.4 17.4 0 0 1-3.2 4.1"
        stroke="currentColor"
        strokeWidth="1.6"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}
