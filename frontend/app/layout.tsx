import "../styles/globals.css";
import { ReactQueryProvider } from "./ReactQueryProvider";
import AuthContext from "./context/AuthContext";

export const metadata = {
  title: {
    default: "Tnsrai",
    template: "Tnsrai | %s"
  },
  description: "Upscale your media (audio, video and images) with AI powered tool on cloud",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <ReactQueryProvider>
      <html lang="en">
        <body>
          <AuthContext>{children}</AuthContext>
        </body>
      </html>
    </ReactQueryProvider>
  );
}
