import { TeamsTab } from "@/components/teams/teams-tab";

// Personal-tab entry point. Sideloading into a real tenant is gated on a Teams app package +
// admin consent (documented in the README); this route builds and runs standalone today.
export default function TeamsTabPage() {
  return <TeamsTab />;
}
