import { createContext, useContext, useEffect, useState, ReactNode } from "react";
import { api, SafeSettings } from "../api/client";

type Ctx = {
  settings: SafeSettings | null;
  reload: () => Promise<void>;
};

const ConfigContext = createContext<Ctx>({ settings: null, reload: async () => {} });

export function ConfigProvider({ children }: { children: ReactNode }) {
  const [settings, setSettings] = useState<SafeSettings | null>(null);

  const reload = async () => {
    setSettings(await api.getSettings());
  };

  useEffect(() => {
    reload();
  }, []);

  return <ConfigContext.Provider value={{ settings, reload }}>{children}</ConfigContext.Provider>;
}

export const useConfig = () => useContext(ConfigContext);
