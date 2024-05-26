const baseURL = process.env.BASEURL;

const dashboardEndpoints = {
  getStats: `${baseURL}/dashboard/get_stats`,
};

const authEndpoints = {
  signup: `${baseURL}/auth/signup`,
  login: `${baseURL}/auth/login`,
  logout: `${baseURL}/auth/logout`,
  verify: `${baseURL}/auth/verify`,
  refresh: `${baseURL}/auth/refresh`,
  googleLogin: `${baseURL}/auth/google/login`,
  googleCallback: `${baseURL}/auth/google/callback`,
  forgotPassword: `${baseURL}/auth/forgotpassword`,
  verifyEmail: `${baseURL}/auth/verifyemail`,
  resetPassword: `${baseURL}/auth/resetpassword`,
};

const uploadEndpoints = {
  generatePresignedPost: `${baseURL}/upload/generate_presigned_post`,
  indexFile: `${baseURL}/upload/indexfile`,
};

const contentEndpoints = {
  getContent: `${baseURL}/content/get_content`,
  contentList: `${baseURL}/content/get_content_list`,
  downloadContent: `${baseURL}/content/download_content`,
  downloadComplete: `${baseURL}/content/download_complete`,
  contentRename: `${baseURL}/content/rename-content`,
};

const settingsEndpoints = {
  changePassword: `${baseURL}/settings/change_password`,
  getSettings: `${baseURL}/settings/get_settings`,
  updateSettings: `${baseURL}/settings/update_settings`,
};

const jobsEndpoints = {
  registerJob: `${baseURL}/jobs/register_job`,
  get_jobs: `${baseURL}/jobs/get_jobs`,
  filterConfig: `${baseURL}/jobs/filter_config`,
  jobEstimate: `${baseURL}/jobs/get_estimate`,
};

const optionsEndpoints = {
  deleteProject: `${baseURL}/options/delete-project`,
  renameProject: `${baseURL}/options/rename-project`,
  resendEmail: `${baseURL}/options/resend-email`,
  userTierConfig: `${baseURL}/options/user_tier`,
};

const billingEndpoints = {
  getBalance: `${baseURL}/billing/get_balance`,
  priceConversion: `${baseURL}/billing/price_conversion`,
  checkout: `${baseURL}/billing/checkout`,
  webhook: `${baseURL}/billing/webhook`,
  getInvoices: `${baseURL}/billing/get_invoices`,
  downloadInvoice: `${baseURL}/billing/download_invoice`,
};

export {
  dashboardEndpoints,
  authEndpoints,
  uploadEndpoints,
  contentEndpoints,
  settingsEndpoints,
  jobsEndpoints,
  optionsEndpoints,
  billingEndpoints,
};
