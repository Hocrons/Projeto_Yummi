import { useId } from "react";
import "./TermsCheckbox.css";

export default function TermsCheckbox({ checked, onChange, error }) {
  const id = useId();

  return (
    <div className="terms">
      <label className="terms__row" htmlFor={id}>
        <input
          id={id}
          type="checkbox"
          className="terms__checkbox"
          checked={checked}
          onChange={(e) => onChange(e.target.checked)}
        />
        <span className="terms__text">
          Ao criar uma conta, você concorda com nossos{" "}
          <a href="#termos" className="terms__link">
            Termos de Uso
          </a>{" "}
          e{" "}
          <a href="#privacidade" className="terms__link">
            Política de Privacidade
          </a>
        </span>
      </label>
      {error ? (
        <p className="field__message field__message--error" role="alert">
          {error}
        </p>
      ) : null}
    </div>
  );
}
