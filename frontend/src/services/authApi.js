import api from "./api";

export async function signupUser(email, password) {
  const response = await api.post("/auth/signup", {
    email,
    password,
  });
  return response.data;
}

export async function loginUser(email, password) {
  const response = await api.post("/auth/login", {
    email,
    password,
  });
  return response.data;
}

export async function getCurrentUser(token) {
  const response = await api.get("/auth/me", {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });
  return response.data;
}