import { useId } from "react";
import "./FormField.css";

export default function FormField({
  label,
  error,
  hint,
  type = "text",
  rightSlot,
  ...inputProps
}) {
  const id = useId();

  return (
    <div className="field">
      <label className="field__label" htmlFor={id}>
        {label}
      </label>
      <div className={`field__control ${error ? "field__control--error" : ""}`}>
        <input id={id} type={type} className="field__input" {...inputProps} />
        {rightSlot}
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
