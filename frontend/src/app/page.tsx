// T-031 — Home page redirect to default admin route.
import { redirect } from "next/navigation";

export default function HomePage() {
  redirect("/admin/suppliers");
}
