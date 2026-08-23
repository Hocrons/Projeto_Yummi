import "./PrimaryButton.css";

export default function PrimaryButton({ children, loading, disabled, ...rest }) {
  return (
    <button className="btn-primary" disabled={disabled || loading} {...rest}>
      {loading ? <span className="btn-primary__spinner" aria-hidden="true" /> : null}
      <span>{loading ? "Enviando..." : children}</span>
    </button>
  );
}
