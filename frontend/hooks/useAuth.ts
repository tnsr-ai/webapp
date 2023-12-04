import { AuthenticationContext } from "../app/context/AuthContext";
import { useContext } from "react";
import { useRouter } from "next/navigation";
import { setCookie } from "cookies-next";

const useAuth = () => {
  const router = useRouter();
  const { data, error, loading, setAuthState } = useContext(
    AuthenticationContext
  );

  const signin = async ({
    email,
    password,
  }: {
    email: string;
    password: string;
  }) => {
    setAuthState({ loading: true, error: null, data: null });
    try {
      setAuthState({ loading: true, error: null, data: null });
      const url: string = `${process.env.BASEURL}/auth/login`;
      const fromData = new FormData();
      fromData.append("username", email);
      fromData.append("password", password);
      const response = await fetch(url, {
        method: "POST",
        body: fromData,
        credentials: "include",
      });
      const data = await response.json();
      if (response.status === 200) {
        router.push("/dashboard");
        setAuthState({
          loading: true,
          error: null,
          data: data.data,
        });
      } else {
        setAuthState({
          loading: false,
          error: data.detail,
          data: null,
        });
      }
    } catch (error: any) {
      setAuthState({
        loading: false,
        error: "Problem occured while login",
        data: null,
      });
    }
  };

  const signup = async ({
    firstname,
    lastname,
    email,
    password,
  }: {
    firstname: string;
    lastname: string;
    email: string;
    password: string;
  }) => {
    try {
      const url: string = `${process.env.BASEURL}/auth/signup`;
      const data = JSON.stringify({
        firstname: firstname,
        lastname: lastname,
        email: email,
        password: password,
      });
      const response = await fetch(url, {
        method: "POST",
        body: data,
        headers: {
          "Content-Type": "application/json",
        },
        credentials: "include",
      });
      const res = await response.json();
      if (response.status === 201) {
        router.push("/dashboard");
        setAuthState({
          loading: true,
          error: null,
          data: res.data,
        });
      } else {
        setAuthState({
          loading: false,
          error: res.detail,
          data: null,
        });
      }
    } catch (error: any) {
      setAuthState({
        loading: false,
        error: "Problem occured while signup",
        data: null,
      });
    }
  };

  const logout = async (jwt: string) => {
    try {
      const url: string = `${process.env.BASEURL}/auth/logout`;
      const response = await fetch(url, {
        method: "GET",
        credentials: "include",
        headers: {
          Authorization: `Bearer ${jwt}`,
        },
      });
      if (response.status === 200) {
        router.push("/");
      } else {
        router.push("/");
      }
    } catch (error: any) {
      null;
    }
  };

  const googleAuth = async () => {
    try {
      const url: string = `${process.env.BASEURL}/auth/google/login`;
      let width = 500;
      let height = 600;
      let left = (screen.width - width) / 2;
      let top = (screen.height - height) / 2;

      const loginWindow = window.open(
        url,
        "Login",
        `width=${width}, height=${height}, top=${top}, left=${left}`
      );
      window.addEventListener("message", function (e) {
        if (e.origin !== process.env.BASEURL) {
          return;
        }
        setCookie("access_token", e.data?.access_token, {
          maxAge: e.data?.access_token_max,
        });
        setCookie("refreshToken", e.data?.refreshToken, {
          maxAge: e.data?.refreshToken_max,
        });
        router.push("/dashboard");
      });
    } catch (error: any) {
      setAuthState({
        loading: false,
        error: "Problem occured while signup",
        data: null,
      });
    }
  };

  return {
    signin,
    signup,
    googleAuth,
    logout,
  };
};

export default useAuth;
