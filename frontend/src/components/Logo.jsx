import "./Logo.css";

export default function Logo({ size = "md" }) {
  return (
    <span className={`logo logo--${size}`}>
      yummi<span className="logo__dot">.</span>
    </span>
  );
}
