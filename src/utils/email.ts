// Mock email sending function
export const sendEmail = async (
  to: string,
  subject: string,
  body: string
): Promise<boolean> => {
  // In a real application, this would use an email service or SMTP server
  console.log('Sending email:');
  console.log(`To: ${to}`);
  console.log(`Subject: ${subject}`);
  console.log(`Body: ${body}`);
  
  // Simulate network delay
  await new Promise(resolve => setTimeout(resolve, 1000));
  
  // Mock successful email sending
  return true;
};

// Send report confirmation email
export const sendReportConfirmation = async (
  userEmail: string,
  userName: string,
  reportId: string,
  reportLocation: string
): Promise<boolean> => {
  const subject = 'Pothole Report Confirmation';
  
  const body = `
    Hello ${userName},
    
    Thank you for reporting a pothole in your area. Your contribution helps make our roads safer for everyone.
    
    Report Details:
    - Report ID: ${reportId}
    - Location: ${reportLocation}
    - Date: ${new Date().toLocaleDateString()}
    
    Your report has been submitted and is pending verification by a government official. Once verified, you will earn points toward your citizen reporter badges.
    
    Thank you for being an active citizen!
    
    Regards,
    The Pothole Reporting Team
  `;
  
  return sendEmail(userEmail, subject, body);
};

// Send verification update email
export const sendVerificationUpdate = async (
  userEmail: string,
  userName: string,
  reportId: string,
  verified: boolean
): Promise<boolean> => {
  const subject = verified 
    ? 'Your Pothole Report Has Been Verified' 
    : 'Update on Your Pothole Report';
  
  const body = verified
    ? `
      Hello ${userName},
      
      Good news! Your pothole report (ID: ${reportId}) has been verified by a government official. You have earned 1 point toward your citizen reporter badges.
      
      Thank you for helping make our roads safer!
      
      Regards,
      The Pothole Reporting Team
    `
    : `
      Hello ${userName},
      
      We have reviewed your pothole report (ID: ${reportId}) and have determined that it does not qualify as a valid report at this time.
      
      This could be due to various reasons such as:
      - The reported issue is not a pothole
      - The location has already been reported
      - Insufficient details in the report
      
      Please continue to report road hazards in your area. Your participation is valuable to our community.
      
      Regards,
      The Pothole Reporting Team
    `;
  
  return sendEmail(userEmail, subject, body);
};