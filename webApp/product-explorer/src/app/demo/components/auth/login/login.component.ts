import { Component, OnInit, OnDestroy, Optional } from '@angular/core';
import { Auth, authState, signInAnonymously, signOut, User, GoogleAuthProvider, signInWithPopup } from '@angular/fire/auth';
import { EMPTY, Observable, Subscription } from 'rxjs';
import { Router } from '@angular/router';
import { LayoutService } from 'src/app/layout/service/app.layout.service';

@Component({
  selector: 'app-login',
  templateUrl: './login.component.html',
  styles: [`
      :host ::ng-deep .pi-eye,
      :host ::ng-deep .pi-eye-slash {
          transform:scale(1.6);
          margin-right: 1rem;
          color: var(--primary-color) !important;
      }
  `]
})
export class LoginComponent implements OnInit {

  valCheck: string[] = ['remember'];
  password!: string;

  private readonly userDisposable: Subscription|undefined;
  public readonly user: Observable<User | null> = EMPTY;


  redirect = ['/'];

  constructor(@Optional() private auth: Auth, public layoutService: LayoutService,  private router: Router) {}

  ngOnInit(): void { }


  async loginWithGoogle() {
    const provider = new GoogleAuthProvider();
    await signInWithPopup(this.auth, provider);
    await this.router.navigate(this.redirect);
  }

}