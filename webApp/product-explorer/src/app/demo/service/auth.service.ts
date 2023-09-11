import { Injectable } from '@angular/core';
import { Router } from '@angular/router';
import { Auth, createUserWithEmailAndPassword, signInWithEmailAndPassword, signInWithPopup, signOut, GoogleAuthProvider, sendPasswordResetEmail, confirmPasswordReset } from '@angular/fire/auth';

@Injectable({
  providedIn: 'root'
})
export class AuthService {

  redirect: string[] = ['/'];  // Default redirect route after successful login

  constructor(private auth: Auth, private router: Router) { }

  // Sign up with email and password
  async signUp(email: string, password: string): Promise<void> {
    try {
      await createUserWithEmailAndPassword(this.auth, email, password);
      await this.router.navigate(this.redirect);
    } catch (error) {
      throw new Error(error.message || 'Error during sign up.');
    }
  }


  // Login with email and password
  async login(email: string, password: string): Promise<void> {
    try {
      await signInWithEmailAndPassword(this.auth, email, password);
      await this.router.navigate(this.redirect);
    } catch (error) {
      throw error;
    }
  }

  // Login with Google
  async loginWithGoogle(): Promise<void> {
    try {
      const provider = new GoogleAuthProvider();
      await signInWithPopup(this.auth, provider);
      await this.router.navigate(this.redirect);
    } catch (error) {
      throw new Error(error.message || 'Error during Google login.');
    }
  }

  // Logout
  async logout(): Promise<void> {
    try {
      await signOut(this.auth);
      await this.router.navigate(['/auth/login']);  // Assuming you have a login route
    } catch (error) {
      throw new Error(error.message || 'Error during logout.');
    }
  }

  async sendPasswordResetEmail(email: string): Promise<void> {
    try {
        await sendPasswordResetEmail(this.auth, email);
    } catch (error) {
        console.error("Forgot Password Error:", error); // Log for debugging
        throw error;
    }
  }

  async confirmPasswordReset(code: string, newPassword: string): Promise<void> {
    try {
        await confirmPasswordReset(this.auth, code, newPassword);
        // Optionally, navigate the user to a different page after resetting the password
        await this.router.navigate(['/login']);  // Assuming you have a login route
    } catch (error) {
        console.error("Password Reset Confirmation Error:", error); // Log for debugging
        throw error;
    }
  }
}
