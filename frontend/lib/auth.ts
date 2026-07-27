export const saveToken = (t: string) => localStorage.setItem("vp_token", t);
export const clearToken = () => localStorage.removeItem("vp_token");
export const getToken = () => localStorage.getItem("vp_token");
export const isLoggedIn = () => !!getToken();
