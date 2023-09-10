import { Component, OnInit, ViewEncapsulation } from '@angular/core';
import { AuthService } from 'src/app/demo/service/auth.service';
import { LayoutService } from 'src/app/layout/service/app.layout.service';
import { MessageService } from 'primeng/api';

@Component({
  selector: 'app-login',
  templateUrl: './login.component.html',
  styleUrls: ['./login.component.scss']
})
export class LoginComponent implements OnInit {

  email: string;
  password: string;
  signupEmail: string;
  signupPassword: string;
  showSignUp = false;
  confirmPassword: string;

  redirect = ['/'];

  constructor(private authService: AuthService, public layoutService: LayoutService, private messageService: MessageService) {}

  ngOnInit(): void { }

  toggleSignUp() {
    this.showSignUp = !this.showSignUp;
  }

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


}