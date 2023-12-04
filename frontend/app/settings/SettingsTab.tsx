"use client";
import { useEffect, useState } from "react";
import { Switch } from "@headlessui/react";
import { Button } from "@mantine/core";
import { setPassword, setSettings } from "../api/index";
import { useMutation } from "@tanstack/react-query";
import { getCookie } from "cookies-next";
import Link from "next/link";

function classNames(...classes: any) {
  return classes.filter(Boolean).join(" ");
}

export default function SettingsTab(props: any) {
  const jwt: string = getCookie("access_token") as string;
  const [newsletter, setNewsletter] = useState(props.data.data["newsletter"]);
  const [enabled, setEnabled] = useState(props.data.data["email_notification"]);
  const [emailMsg, setEmailMsg] = useState(
    "Click here to resend verification email"
  );
  const [emailStatus, setEmailStatus] = useState("text-blue-500");
  const { mutate } = useMutation((formData) => setPassword(formData as any), {
    onSuccess: (data) => {
      if (data["detail"] != "Success") {
        setSuccess("");
        setError(data["data"]);
        return;
      } else {
        setSuccess("Password changed successfully");
        setError("");
      }
    },
    onError: (error: any) => {
      setError(error.data.message);
    },
  });

  const settingsPost = useMutation((formData) => setSettings(formData as any), {
    onSuccess: (data) => {
      if (data["detail"] != "Success") {
        setSuccessSetting("");
        setErrorSetting(data["data"]);
        return;
      } else {
        setSuccessSetting("Settings changed successfully");
        setErrorSetting("");
        setChanged(false);
      }
    },
    onError: (error: any) => {
      setError(error.data.message);
    },
  });

  const [changed, setChanged] = useState(false);

  const default_notification = {
    newsletter: props.data.data["newsletter"],
    email_notification: props.data.data["email_notification"],
    discord_webhook: props.data.data["discord_webhook"],
  };

  const [notificationSettings, setNotificationSettings] = useState({
    newsletter: props.data.data["newsletter"],
    email_notification: props.data.data["email_notification"],
    discord_webhook: props.data.data["discord_webhook"],
  });

  const [inputs, setInputs] = useState({
    currentPassword: "",
    newPassword: "",
    confirmPassword: "",
  });

  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [passwordPass, setPasswordPass] = useState(false);

  const [errorSetting, setErrorSetting] = useState("");
  const [successSetting, setSuccessSetting] = useState("");

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setInputs({
      ...inputs,
      [e.target.name]: e.target.value,
    });
  };

  const handleNotificationChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setNotificationSettings({
      ...notificationSettings,
      [e.target.name]: e.target.value,
    });
  };

  const changePassword = () => {
    if (inputs.newPassword !== inputs.confirmPassword) {
      setError("Passwords do not match");
      return;
    }
    const formData = {
      current_password: inputs.currentPassword,
      new_password: inputs.newPassword,
      confirm_password: inputs.confirmPassword,
    };

    mutate(formData as any);
  };

  const updateSettings = () => {
    const formData = {
      newsletter: newsletter,
      email_notification: enabled,
      discord_webhook: notificationSettings.discord_webhook,
    };
    settingsPost.mutate(formData as any);
  };

  const resendTask = useMutation(({ id }: { id: number }) => {
    const url = `${process.env.BASEURL}/options/resend-email`;
    return fetch(url, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${jwt}`,
      },
    });
  });

  useEffect(() => {
    if (
      inputs.newPassword.length != 0 &&
      inputs.confirmPassword.length != 0 &&
      inputs.currentPassword.length != 0
    ) {
      if (inputs.currentPassword === inputs.newPassword) {
        setError("New password cannot be the same as current password");
      }
      if (inputs.newPassword !== inputs.confirmPassword) {
        setError("Passwords do not match");
      }
      if (inputs.newPassword.length < 8) {
        setError("Password must be at least 8 characters long");
      }
      if (
        inputs.currentPassword.length >= 8 &&
        inputs.newPassword.length >= 8 &&
        inputs.confirmPassword.length >= 8 &&
        inputs.newPassword === inputs.confirmPassword &&
        inputs.currentPassword !== inputs.newPassword
      ) {
        setError("");
        setPasswordPass(true);
      }
    } else {
      setError("");
      setPasswordPass(false);
    }
    if (
      JSON.stringify(notificationSettings) !==
        JSON.stringify(default_notification) ||
      default_notification.newsletter !== newsletter ||
      default_notification.email_notification !== enabled
    ) {
      setChanged(true);
    } else {
      setChanged(false);
    }
  }, [
    inputs,
    notificationSettings,
    newsletter,
    enabled,
    emailMsg,
    emailStatus,
  ]);

  return (
    <div className="max-w-[1500px] m-auto">
      <div>
        <h1 className="text-2xl font-semibold ml-5 mb-5">Settings</h1>
      </div>
      <div className="grid grid-cols-1 xl:grid-cols-2 px-6 gap-5">
        <div id="userprofile">
          <div className="w-[100%] bg-zinc-200 py-6 rounded-2xl" id="nameTab">
            <div className="grid grid-cols-2 gap-5 px-6">
              <div>
                <label className="font-medium tracking-tight">First Name</label>
                <input
                  type="text"
                  value={props.data.data["first_name"]}
                  className="w-full mt-2 px-3 py-2 text-gray-500 outline-transparent border-transparent focus:bg-gray-200 focus:ring-0 focus:border-transparent shadow-sm rounded-lg bg-gray-50"
                  disabled
                />
              </div>
              <div>
                <label className="font-medium tracking-tight">Last Name</label>
                <input
                  type="text"
                  value={props.data.data["last_name"]}
                  className="w-full mt-2 px-3 py-2 text-gray-500 outline-transparent border-transparent focus:bg-gray-200 focus:ring-0 focus:border-transparent shadow-sm rounded-lg bg-gray-50"
                  disabled
                />
              </div>
            </div>
            <div className="px-6 mt-5" id="emailTab">
              <div className="flex space-x-2">
                <label className="font-medium tracking-tight">Email</label>
                {props.data.verified === false && (
                  <div className="flex space-x-2">
                    <p className="font-medium tracking-tight text-red-500">
                      (Not Verified)
                    </p>
                    <p
                      className={`font-medium tracking-tight cursor-pointer ${emailStatus}`}
                      onClick={() => {
                        resendTask.mutate({ id: 1 });
                        setEmailMsg("Email sent");
                        setEmailStatus("text-green-500");
                      }}
                    >
                      {emailMsg}
                    </p>
                  </div>
                )}
                {props.data.verified === true && (
                  <div>
                    <p className="font-medium tracking-tight text-green-500">
                      (Verified)
                    </p>
                  </div>
                )}
              </div>
              <input
                type="email"
                className="w-full mt-2 px-3 py-2 text-gray-500 outline-transparent border-transparent focus:bg-gray-200 focus:ring-0 focus:border-transparent shadow-sm rounded-lg bg-gray-50"
                value={props.data.data["email"]}
                disabled
              />
            </div>
            <div id="passwordTab">
              <div className="px-6 mt-3">
                <label className="font-medium tracking-tight">
                  Current Password
                </label>
                <input
                  type="password"
                  name="currentPassword"
                  onChange={handleChange}
                  required
                  className="w-full mt-2 px-3 py-2 text-gray-500 outline-transparent border-transparent focus:bg-gray-200 focus:ring-0 focus:border-transparent shadow-sm rounded-lg bg-gray-50"
                />
              </div>
              <div className="px-6 mt-3">
                <label className="font-medium tracking-tight">
                  New Password
                </label>
                <input
                  type="password"
                  name="newPassword"
                  onChange={handleChange}
                  required
                  className="w-full mt-2 px-3 py-2 text-gray-500 outline-transparent border-transparent focus:bg-gray-200 focus:ring-0 focus:border-transparent shadow-sm rounded-lg bg-gray-50"
                />
              </div>
              <div className="px-6 mt-3">
                <label className="font-medium tracking-tight">
                  Confirm Password
                </label>
                <input
                  type="password"
                  name="confirmPassword"
                  onChange={handleChange}
                  required
                  className="w-full mt-2 px-3 py-2 text-gray-500 outline-transparent border-transparent focus:bg-gray-200 focus:ring-0 focus:border-transparent shadow-sm rounded-lg bg-gray-50"
                />
                <div>
                  {error.length > 0 && (
                    <p className="mt-3 font-normal md:font-medium whitespace-nowrap text-red-500">
                      {error}
                    </p>
                  )}
                  {success.length > 0 && (
                    <p className="mt-3 font-normal md:font-medium whitespace-nowrap text-green-500">
                      {success}
                    </p>
                  )}
                </div>
                <div className="mt-5">
                  {passwordPass && (
                    <Button
                      variant="outline"
                      color="grape"
                      size="sm"
                      onClick={changePassword}
                    >
                      Save
                    </Button>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>
        <div id="notification" className="bg-zinc-200 w-[100%] rounded-2xl">
          <h1 className="text-black font-medium text-xl p-6">Notification</h1>
          <div className="px-6 flex gap-3" id="newsletter">
            <Switch
              data-testid="newsletterSwitch"
              checked={newsletter}
              onChange={setNewsletter}
              className={classNames(
                newsletter ? "bg-purple-600" : "bg-gray-400",
                "relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-offset-2"
              )}
            >
              <span className="sr-only">Use setting</span>
              <span
                aria-hidden="true"
                className={classNames(
                  newsletter ? "translate-x-5" : "translate-x-0",
                  "pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out"
                )}
              />
            </Switch>
            <h1 className="text-black font-normal text-lg">
              Send Newsletter and Updates Notification
            </h1>
          </div>
          <div className="px-6 flex gap-3 mt-5" id="emailSwitch">
            <Switch
              checked={enabled}
              onChange={setEnabled}
              className={classNames(
                enabled ? "bg-purple-600" : "bg-gray-400",
                "relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-offset-2"
              )}
            >
              <span className="sr-only">Use setting</span>
              <span
                aria-hidden="true"
                className={classNames(
                  enabled ? "translate-x-5" : "translate-x-0",
                  "pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out"
                )}
              />
            </Switch>
            <h1 className="text-black font-normal text-lg">
              Send Email Notification
            </h1>
          </div>
          <div className="px-6 mt-5 mb-5 xl:mb-0" id="emailTab">
            <p className="font-medium tracking-tight">
              Discord Webhook{" "}
              <Link
                href={
                  "https://support.discord.com/hc/en-us/articles/228383668-Intro-to-Webhooks"
                }
                className="font-medium tracking-tight text-purple-400"
                target="_blank"
              >
                *
              </Link>
            </p>
            <input
              type="text"
              className="w-full mt-2 px-3 py-2 text-gray-500 outline-transparent border-transparent focus:bg-gray-200 focus:ring-0 focus:border-transparent shadow-sm rounded-lg bg-gray-50"
              name="discord_webhook"
              defaultValue={props.data.data["discord_webhook"]}
              onChange={handleNotificationChange}
            />
            <div>
              {errorSetting.length > 0 && (
                <p className="mt-3 font-normal md:font-medium whitespace-nowrap text-red-500">
                  {errorSetting}
                </p>
              )}
              {successSetting.length > 0 && (
                <p className="mt-3 font-normal md:font-medium whitespace-nowrap text-green-500">
                  {successSetting}
                </p>
              )}
            </div>
            {changed && (
              <Button
                variant="outline"
                color="grape"
                size="sm"
                onClick={updateSettings}
                className="mt-3"
              >
                Update
              </Button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
