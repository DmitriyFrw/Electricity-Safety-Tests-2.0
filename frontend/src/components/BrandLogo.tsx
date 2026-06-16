import { Link } from "react-router-dom";

const SIDEBAR_LOGO_SRC = "/razvivaisia/assets/images/razvivaisia-logo.png";

type Props = {
  className?: string;
  variant?: "default" | "sidebar";
};

export default function BrandLogo({ className = "", variant = "default" }: Props) {
  if (variant === "sidebar") {
    return (
      <Link to="/" className={`brand-logo brand-logo--sidebar ${className}`.trim()}>
        <img src={SIDEBAR_LOGO_SRC} alt="Развивайся" className="brand-logo__img" width={400} height={170} />
      </Link>
    );
  }

  return (
    <Link to="/" className={`brand-logo ${className}`.trim()}>
      <span className="brand-logo__mark" aria-hidden="true">
        Y
      </span>
      <span className="brand-logo__text">Развивайся</span>
    </Link>
  );
}
