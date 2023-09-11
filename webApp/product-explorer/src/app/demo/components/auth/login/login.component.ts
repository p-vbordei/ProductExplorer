import { Component, OnInit, ViewEncapsulation } from '@angular/core';
import { AuthService } from 'src/app/demo/service/auth.service';
import { LayoutService } from 'src/app/layout/service/app.layout.service';
import { MessageService } from 'primeng/api';

export enum AuthState {
  LOGIN = 'LOGIN',
  SIGNUP = 'SIGNUP',
  FORGOT_PASSWORD = 'FORGOT_PASSWORD',
  RESET_PASSWORD = 'RESET_PASSWORD'
}

@Component({
  selector: 'app-login',
  templateUrl: './login.component.html',
  styleUrls: ['./login.component.scss']
})
export class LoginComponent implements OnInit {
  //0;vVjiD724M=
  currentState: AuthState = AuthState.LOGIN;
  AuthState = AuthState;
  resetCode: string;
  email: string;
  forgotEmail: string;
  password: string;
  newPassword: string;
  confirmNewPassword: string;
  signupEmail: string;
  signupPassword: string;
  confirmPassword: string;

  redirect = ['/'];

  constructor(private authService: AuthService, public layoutService: LayoutService, private messageService: MessageService) {}

  ngOnInit(): void { }

  async loginWithGoogle() {
    try {
      await this.authService.loginWithGoogle();
      this.messageService.add({severity:'success', summary: 'Success', detail: 'Logged in with Google'});
    } catch (error) {
      this.messageService.add({severity:'error', summary: 'Error', detail: error.message || 'Error logging in with Google'});
    }
  }

  async signUp() { 
    if (this.signupPassword !== this.confirmPassword) {
      this.messageService.add({severity:'error', summary: 'Error', detail: 'Passwords do not match!'});
      return;
    }
    try {
      await this.authService.signUp(this.signupEmail, this.signupPassword);
      this.messageService.add({severity:'success', summary: 'Success', detail: 'Account created successfully'});
    } catch (error) {
      this.messageService.add({severity:'error', summary: 'Error', detail: error.message || 'Error creating account'});
    }
  }

  async login() {
    try {
        await this.authService.login(this.email, this.password);
        this.messageService.add({severity:'success', summary: 'Success', detail: 'Logged in successfully'});
    } catch (error) {
        this.messageService.add({severity:'error', summary: 'Error', detail: error.message || 'Error logging in'});
    }
  }

  async sendResetEmail() {
    try {
      // Assuming you have a method in your AuthService to send the reset email
      await this.authService.sendPasswordResetEmail(this.forgotEmail);
      this.messageService.add({severity:'success', summary: 'Success', detail: 'Reset email sent!'});
      this.currentState = AuthState.LOGIN; // Move to the next step
    } catch (error) {
      this.messageService.add({severity:'error', summary: 'Error', detail: error.message});
    }
  }
  
  async onConfirmPasswordReset() {
    if (this.newPassword !== this.confirmNewPassword) {
      this.messageService.add({severity:'error', summary: 'Error', detail: 'Passwords do not match!'});
      return;
    }
    try {
      await this.authService.confirmPasswordReset(this.resetCode, this.newPassword);
      this.messageService.add({severity:'success', summary: 'Success', detail: 'Password has been reset successfully!'});
      this.currentState = AuthState.LOGIN; // Go back to the login view
    } catch (error) {
      this.messageService.add({severity:'error', summary: 'Error', detail: error.message});
    }
  }


}